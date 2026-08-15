from aiogram import Router, F
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from keyboards.inline import premium_plans_keyboard
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
    text = f"Премиум: {status}{expiry}\n\nВыберите план:"
    if delete_old:
        await target.delete()
    await target.answer(text, reply_markup=premium_plans_keyboard())

async def show_premium_for_message(message: Message, session: AsyncSession):
    await show_premium(message, message.from_user.id, session, delete_old=False)

@router.callback_query(F.data.startswith("premium_"))
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