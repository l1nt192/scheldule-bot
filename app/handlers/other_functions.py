from aiogram.types import Message, CallbackQuery
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import app.keyboards.registration_kb as registration_kb
from app.state.states import RegistrationStates
from app.utils.messages.safe_delete_messages import safe_delete_message, safe_delete_callback_message
from app.database.db import AsyncSessionLocal
from app.database.models import User
from sqlalchemy import delete
from app.keyboards.main_menu_kb import get_main_menu_kb
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "Прочие функции")
async def other_functions(message: Message):
    """Меню прочих функций"""
    await safe_delete_message(message)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Изменить персональные данные", callback_data="change_personal_data")],
            [InlineKeyboardButton(text="Выйти из профиля", callback_data="logout")],
            [InlineKeyboardButton(text="Назад", callback_data="exit_other_functions")]
        ]
    )
    await message.answer("Выберите действие:", reply_markup=kb)


@router.callback_query(F.data == "change_personal_data")
async def change_personal_data(callback: CallbackQuery, state: FSMContext):
    """Запуск процесса изменения персональных данных"""
    await callback.message.edit_text("Выберите ваш факультет:", reply_markup=registration_kb.faculty_keyboard_reg)
    await state.set_state(RegistrationStates.choice_faculty)
    await callback.answer()


@router.callback_query(F.data == "logout")
async def logout_user(callback: CallbackQuery):
    """Выход из профиля - удаление пользователя из базы данных"""
    try:
        user_id = callback.from_user.id

        async with AsyncSessionLocal() as session:
            # Проверяем, существует ли пользователь
            from sqlalchemy import select
            query = await session.execute(select(User).where(User.id == user_id))
            existing_user = query.scalars().first()

            if not existing_user:
                await callback.answer("❌ Вы не зарегистрированы!", show_alert=True)
                return

            # Удаляем пользователя из базы данных
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()

        # Получаем клавиатуру для незарегистрированного пользователя
        updated_keyboard = await get_main_menu_kb(user_id)

        # Удаляем текущее сообщение с меню
        await callback.message.delete()

        # Отправляем новое сообщение с обновленной клавиатурой
        await callback.message.answer(
            "✅ Вы вышли из профиля.\n\n"
            "Теперь у вас доступен ограниченный функционал. "
            "Для доступа ко всем функциям пройдите регистрацию.",
            reply_markup=updated_keyboard
        )

    except Exception as e:
        logger.error(f"Ошибка при выходе из профиля: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка при выходе из профиля", show_alert=True)


@router.callback_query(F.data == "exit_other_functions")
async def exit_other_functions(callback: CallbackQuery):
    """Выход из меню прочих функций"""
    await safe_delete_callback_message(callback)