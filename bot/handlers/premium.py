from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, SuccessfulPayment
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from database import crud
from config import config
from keyboards.inline import premium_payment_methods_keyboard, premium_stars_plans_keyboard, premium_features_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "premium")
async def premium_menu(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    text = "💎 Премиум-подписка\n\n"
    if user.is_premium and user.premium_expiry and user.premium_expiry > datetime.utcnow():
        text += f"У вас активна подписка до {user.premium_expiry.strftime('%d.%m.%Y %H:%M')}."
    else:
        text += "Выберите способ оплаты:"
    await callback.message.edit_text(text, reply_markup=premium_payment_methods_keyboard())
    await callback.answer()

async def show_premium_for_message(message: Message, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Зарегистрируйтесь через /start")
        return
    text = "💎 Премиум-подписка\n\n"
    if user.is_premium and user.premium_expiry and user.premium_expiry > datetime.utcnow():
        text += f"У вас активна подписка до {user.premium_expiry.strftime('%d.%m.%Y %H:%M')}."
    else:
        text += "Выберите способ оплаты:"
    await message.answer(text, reply_markup=premium_payment_methods_keyboard())

@router.callback_query(F.data == "premium_stars")
async def premium_stars(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь")
        return
    await callback.message.edit_text("Выберите тариф (оплата звёздами):", reply_markup=premium_stars_plans_keyboard())
    await callback.answer()

@router.callback_query(F.data == "premium_card")
async def premium_card(callback: CallbackQuery):
    text = (
        "💳 Оплата картой / СБП\n\n"
        "Тарифы:\n"
        "• 1 месяц – 150 ₽\n"
        "• 3 месяца – 350 ₽\n\n"
        "⚠️ Оплата картой временно недоступна. Ведутся технические работы.\n"
        "Приносим извинения за неудобства."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="premium")]
    ])
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data.startswith("premium_stars_"))
async def premium_stars_plan(callback: CallbackQuery, session: AsyncSession):
    plan = callback.data.split("_")[2]
    months = int(plan)
    star_prices = {1: 100, 3: 250}
    price_in_stars = star_prices.get(months, 100)
    base_price_rub = 150 if months == 1 else 350

    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Ошибка")
        return

    final_price_rub = await crud.apply_referral_discount(session, user.id, base_price_rub)
    discount = user.referral_discount or 0

    text = f"Тариф на {months} месяц(ев) – {price_in_stars} ⭐\n"
    if discount > 0:
        text += f"Ваша скидка: {discount}% (без скидки: {base_price_rub} ₽, со скидкой: {final_price_rub} ₽)\n"
    text += "\nНажмите «Оплатить» для продолжения."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Оплатить", callback_data=f"stars_pay_{months}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="premium_stars")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("stars_pay_"))
async def stars_pay(callback: CallbackQuery, session: AsyncSession):
    months = int(callback.data.split("_")[2])
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Ошибка")
        return
    star_prices = {1: 100, 3: 250}
    price_in_stars = star_prices.get(months, 100)
    price_in_stars = await crud.apply_referral_discount(session, user.id, price_in_stars)
    price_in_stars = max(price_in_stars, 1)
    prices = [LabeledPrice(label="Премиум", amount=price_in_stars)]
    try:
        await callback.bot.send_invoice(
            chat_id=callback.from_user.id,
            title="Премиум-подписка MuseTwin",
            description=f"Доступ к премиум-функциям на {months} месяц(ев)",
            payload=f"premium_{months}_{user.id}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="premium_subscription",
            need_name=False,
            need_email=False,
            need_phone_number=False,
        )
    except Exception as e:
        logger.error(f"Stars invoice error: {e}")
        await callback.message.edit_text("Ошибка при создании счёта. Попробуйте позже.")
    await callback.answer()

@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: Message, session: AsyncSession):
    payment = message.successful_payment
    payload = payment.invoice_payload
    parts = payload.split("_")
    if len(parts) >= 3:
        months = int(parts[1])
        user_id = int(parts[2])
        user = await crud.get_user_by_id(session, user_id)
        if user:
            await crud.set_premium(session, user_id, months)
            await crud.record_payment(
                session, user_id, payment.telegram_payment_charge_id,
                payment.total_amount, months,
                datetime.utcnow() + timedelta(days=30*months)
            )
            await message.answer(f"🎉 Премиум активирован на {months} месяц(ев)!")
            for admin_id in config.ADMIN_IDS:
                try:
                    await message.bot.send_message(admin_id, f"💰 Покупка премиум: {user.name or user.username} на {months} мес.")
                except:
                    pass
        else:
            await message.answer("Ошибка активации. Обратитесь к @danhooks.")
    else:
        await message.answer("Ошибка оплаты.")

@router.callback_query(F.data == "premium_back")
async def premium_back(callback: CallbackQuery, session: AsyncSession):
    await premium_menu(callback, session)