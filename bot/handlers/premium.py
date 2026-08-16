from aiogram import Router, F
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from keyboards.reply import main_reply_keyboard
from utils.payments import PLANS, create_invoice_payload, get_premium_expiry
from config import config

router = Router()

@router.callback_query(F.data == "premium")
async def premium_show(callback: CallbackQuery, session: AsyncSession):
    await show_premium(callback.message, callback.from_user.id, session, delete_old=True)
    await callback.answer()

async def show_premium(target: Message, user_id: int, session: AsyncSession, delete_old: bool = False):
    user = await crud.get_user_by_telegram_id(session, user_id)
    if not user:
        await target.answer("Зарегистрируйтесь через /start")
        return
    status = "Активен" if user.is_premium else "Неактивен"
    expiry = f" (до {user.premium_expiry.strftime('%Y-%m-%d')})" if user.premium_expiry else ""
    text = f"⭐ Премиум: {status}{expiry}\n\nВыберите план:"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 месяц – 100 ⭐", callback_data="premium_1")],
        [InlineKeyboardButton(text="3 месяца – 250 ⭐", callback_data="premium_3")],
        [InlineKeyboardButton(text="Доступные премиум-функции", callback_data="show_premium_features")],
        [InlineKeyboardButton(text="Назад", callback_data="main_menu")]
    ])
    if delete_old:
        await target.delete()
    await target.answer(text, reply_markup=kb)

async def show_premium_for_message(message: Message, session: AsyncSession):
    await show_premium(message, message.from_user.id, session, delete_old=False)

@router.callback_query(F.data.startswith("premium_1") | F.data.startswith("premium_3"))
async def premium_plan(callback: CallbackQuery, session: AsyncSession):
    plan_key = callback.data.split("_")[1]
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