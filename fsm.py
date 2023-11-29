from aiogram.fsm.state import State, StatesGroup

# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMPost(StatesGroup):
    fill_name = State()
    fill_description = State()
    fill_price = State()
    fill_photo = State()
    approve = State()

class FSMZakaz(StatesGroup):
    fill_zakaz = State()

class FSMSettings(StatesGroup):
    fill_settings = State()
    fill_podval = State()
    fill_token = State()
    fill_group = State()