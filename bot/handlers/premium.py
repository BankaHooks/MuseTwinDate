from aiogram import Router, F
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from keyboards.reply import main_reply_keyboard
from utils.payments import PLANS, create_invoice_payload, get_premium_expiry
from config import config
from keyboards.inline import (
    premium_payment_methods_keyboard,
    premium_stars_plans_keyboard,
    premium_rub_plans_keyboard,
    main_menu_keyboard
)

router = Router()

@router.callback_query(F.data == "premium")
async def premium_show(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    status = "Активен" if user.is_premium else "Неактивен"
    expiry = f" (до {user.premium_expiry.strftime('%Y-%m-%d')})" if user.premium_expiry else ""
    text = f"⭐ Премиум: {status}{expiry}\n\nВыберите способ оплаты:"
    await callback.message.edit_text(text, reply_markup=premium_payment_methods_keyboard())
    await callback.answer()

@router.callback_query(F.data == "premium_back")
async def premium_back(callback: CallbackQuery):
    await premium_show(callback, None)  # session не нужен для клавиатуры, но для функции нужен, передаём None

@router.callback_query(F.data == "premium_stars")
async def premium_stars_method(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите тариф в звёздах:",
        reply_markup=premium_stars_plans_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "premium_card")
async def premium_card_method(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите тариф в рублях (оплата картой / СБП):",
        reply_markup=premium_rub_plans_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("premium_stars_"))
async def premium_stars_plan(callback: CallbackQuery, session: AsyncSession):
    plan_key = callback.data.split("_")[2]
    if plan_key not in ["1", "3"]:
        await callback.answer("Неверный план.")
        return
    plan = PLANS.get(plan_key)
    if not plan:
        await callback.answer("Неверный план.")
        return
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    payload = create_invoice_payload(plan_key, user.id)
    prices = [LabeledPrice(label=plan["label"], amount=plan["price"])]
    try:
        await callback.bot.send_invoice(
            chat_id=callback.from_user.id,
            title="MuseTwinDate Premium",
            description=f"Premium подписка на {plan['label']}",
            payload=payload,
            provider_token=config.PAYMENT_PROVIDER_TOKEN,
            currency="XTR",
            prices=prices,
            start_parameter="premium",
        )
        await callback.answer()
    except Exception as e:
        await callback.answer("Ошибка при создании счёта. Попробуйте позже.", show_alert=True)
        print(f"Invoice error: {e}")

@router.callback_query(F.data.startswith("premium_rub_"))
async def premium_rub_plan(callback: CallbackQuery):
    plan_key = callback.data.split("_")[2]
    if plan_key == "1":
        price = "150 ₽"
        plan_desc = "1 месяц"
    elif plan_key == "3":
        price = "350 ₽"
        plan_desc = "3 месяца"
    else:
        await callback.answer("Неверный план.")
        return
    await callback.answer(
        f"Оплата картой временно недоступна.\n"
        f"Вы выбрали тариф: {plan_desc} за {price}.\n"
        f"Пожалуйста, используйте оплату звёздами.",
        show_alert=True
    )
    await callback.message.edit_text(
        "Оплата картой временно недоступна.\n"
        "Выберите оплату через Telegram Stars.",
        reply_markup=premium_stars_plans_keyboard()
    )

@router.pre_checkout_query()
async def pre_checkout(pre_checkout: PreCheckoutQuery):
    await pre_checkout.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: Message, session: AsyncSession):
    payment = message.successful_payment
    parts = payment.invoice_payload.split("_")
    if len(parts) >= 3 and parts[0] == "premium":
        plan_key = parts[1]
        user_id = int(parts[2])
        plan = PLANS.get(plan_key)
        if plan:
            expiry = get_premium_expiry(plan["months"])
            await crud.record_payment(session, user_id, payment.telegram_payment_charge_id,
                                      payment.total_amount, plan["months"], expiry)
            await crud.set_premium(session, user_id, plan["months"])
            await message.answer("Премиум активирован! Спасибо.", reply_markup=main_reply_keyboard())
            return
    await message.answer("Платёж записан, но что-то пошло не так. Обратитесь в поддержку.")