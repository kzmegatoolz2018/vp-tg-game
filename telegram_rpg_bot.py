#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram RPG Adventure Bot
A choose-your-own-adventure style RPG bot for Telegram
Based on pyTelegramBotAPI library

To install dependencies:
pip install pyTelegramBotAPI

Replace 'YOUR_BOT_TOKEN_HERE' with your actual bot token from @BotFather
"""

import telebot
from telebot import types
import json
import os
import redis

# Initialize bot with placeholder token
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
bot = telebot.TeleBot(BOT_TOKEN)

# Redis connection for persistent storage
try:
    # Try connecting to Redis service (in Docker) or localhost
    redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, db=0, decode_responses=True)
    # Test connection
    redis_client.ping()
    print("Connected to Redis successfully")
except:
    # Fallback to in-memory storage if Redis is not available
    print("Redis not available, using in-memory storage")
    redis_client = None

def load_player_data():
    """Load player data from Redis if available"""
    global redis_client
    if redis_client:
        try:
            # Get all keys with 'player:' prefix
            player_keys = redis_client.keys('player:*')
            player_states = {}
            for key in player_keys:
                try:
                    data = redis_client.get(key)
                    if data:
                        player_states[key.replace('player:', '')] = json.loads(data)
                except:
                    continue
            return player_states
        except Exception as e:
            print(f"Error loading player data from Redis: {e}")
    return {}

def save_player_data(chat_id, data):
    """Save player data to Redis"""
    global redis_client
    if redis_client:
        try:
            redis_client.setex(f'player:{chat_id}', 86400, json.dumps(data, ensure_ascii=False))  # Expire after 24 hours
            return True
        except Exception as e:
            print(f"Error saving player data to Redis: {e}")
            return False
    return False

def get_player_state(chat_id):
    """Get or initialize player state"""
    str_chat_id = str(chat_id)
    
    if redis_client:
        # Try to get from Redis
        data = redis_client.get(f'player:{str_chat_id}')
        if data:
            return json.loads(data)
        else:
            # Initialize new player state
            new_state = {
                'current_scene': 'start',
                'inventory': [],
                'health': 100,
                'experience': 0
            }
            save_player_data(str_chat_id, new_state)
            return new_state
    else:
        # Fallback to in-memory storage
        if not hasattr(get_player_state, 'player_states'):
            get_player_state.player_states = {}
        if str_chat_id not in get_player_state.player_states:
            get_player_state.player_states[str_chat_id] = {
                'current_scene': 'start',
                'inventory': [],
                'health': 100,
                'experience': 0
            }
        return get_player_state.player_states[str_chat_id]

def update_player_state(chat_id, key, value):
    """Update a specific field in player state"""
    str_chat_id = str(chat_id)
    player_state = get_player_state(str_chat_id)
    player_state[key] = value
    
    if redis_client:
        save_player_data(str_chat_id, player_state)
    else:
        # Update in-memory storage
        if hasattr(get_player_state, 'player_states'):
            get_player_state.player_states[str_chat_id] = player_state

def add_to_inventory(chat_id, item):
    """Add an item to player's inventory"""
    str_chat_id = str(chat_id)
    player_state = get_player_state(str_chat_id)
    
    if item not in player_state['inventory']:
        player_state['inventory'].append(item)
        
        if redis_client:
            save_player_data(str_chat_id, player_state)
        else:
            # Update in-memory storage
            if hasattr(get_player_state, 'player_states'):
                get_player_state.player_states[str_chat_id] = player_state
        
        return True
    return False

def reset_player_state(chat_id):
    """Reset player state to initial values"""
    str_chat_id = str(chat_id)
    new_state = {
        'current_scene': 'start',
        'inventory': [],
        'health': 100,
        'experience': 0
    }
    
    if redis_client:
        save_player_data(str_chat_id, new_state)
    else:
        # Update in-memory storage
        if not hasattr(get_player_state, 'player_states'):
            get_player_state.player_states = {}
        get_player_state.player_states[str_chat_id] = new_state

def get_inventory_message(inventory):
    """Format inventory as a readable message"""
    if not inventory:
        return "Ваш инвентарь пуст."
    
    items_list = "\n".join([f"- {item}" for item in inventory])
    return f"Ваш инвентарь:\n{items_list}"

def create_main_menu_keyboard():
    """Create the main menu keyboard with choices"""
    keyboard = types.InlineKeyboardMarkup()
    
    # Create buttons for main choices
    btn1 = types.InlineKeyboardButton("Исследовать лесную тропу", callback_data='choice_forest')
    btn2 = types.InlineKeyboardButton("Войти в руины древнего замка", callback_data='choice_castle')
    btn3 = types.InlineKeyboardButton("Поговорить с деревенским старостой", callback_data='choice_village_head')
    btn4 = types.InlineKeyboardButton("Проверить инвентарь", callback_data='check_inventory')
    
    keyboard.row(btn1)
    keyboard.row(btn2)
    keyboard.row(btn3)
    keyboard.row(btn4)
    
    return keyboard

def create_back_to_menu_keyboard():
    """Create a keyboard with just a back to main menu button"""
    keyboard = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("← Вернуться в главное меню", callback_data='main_menu')
    keyboard.row(btn)
    return keyboard

def create_scene_forest_keyboard():
    """Create keyboard for forest scene choices"""
    keyboard = types.InlineKeyboardMarkup()
    
    btn1 = types.InlineKeyboardButton("Продолжить по тропе", callback_data='forest_path_continue')
    btn2 = types.InlineKeyboardButton("Свернуть в сторону ручья", callback_data='forest_stream')
    btn3 = types.InlineKeyboardButton("Искать ягоды", callback_data='forest_berries')
    
    keyboard.row(btn1)
    keyboard.row(btn2, btn3)
    
    return keyboard

def create_scene_castle_keyboard():
    """Create keyboard for castle scene choices"""
    keyboard = types.InlineKeyboardMarkup()
    
    btn1 = types.InlineKeyboardButton("Подняться по лестнице", callback_data='castle_stairs')
    btn2 = types.InlineKeyboardButton("Обыскать зал", callback_data='castle_hall_search')
    btn3 = types.InlineKeyboardButton("Проверить подозрительную дверь", callback_data='castle_door')
    
    keyboard.row(btn1)
    keyboard.row(btn2, btn3)
    
    return keyboard

def create_scene_village_head_keyboard():
    """Create keyboard for village head scene choices"""
    keyboard = types.InlineKeyboardMarkup()
    
    btn1 = types.InlineKeyboardButton("Спросить о местных легендах", callback_data='village_legends')
    btn2 = types.InlineKeyboardButton("Попросить совет", callback_data='village_advice')
    btn3 = types.InlineKeyboardButton("Предложить помощь", callback_data='village_help')
    
    keyboard.row(btn1)
    keyboard.row(btn2, btn3)
    
    return keyboard

def create_puzzle_solution_keyboard():
    """Create keyboard for puzzle solution"""
    keyboard = types.InlineKeyboardMarkup()
    
    btn1 = types.InlineKeyboardButton("17", callback_data='puzzle_wrong')
    btn2 = types.InlineKeyboardButton("23", callback_data='puzzle_correct')
    btn3 = types.InlineKeyboardButton("31", callback_data='puzzle_wrong')
    
    keyboard.row(btn1, btn2, btn3)
    
    return keyboard

def create_battle_choice_keyboard():
    """Create keyboard for battle choices"""
    keyboard = types.InlineKeyboardMarkup()
    
    btn1 = types.InlineKeyboardButton("Сражаться", callback_data='battle_fight')
    btn2 = types.InlineKeyboardButton("Бежать", callback_data='battle_run')
    
    keyboard.row(btn1, btn2)
    
    return keyboard

@bot.message_handler(commands=['start'])
def start_command(message):
    """
    Handle the /start command
    Resets player state and sends welcome message
    """
    try:
        # Reset player state
        reset_player_state(message.chat.id)
        
        # Create welcome message
        welcome_msg = (
            "Добро пожаловать в Eldoria! 🌲🏰\n\n"
            "Вы — смелый искатель приключений, который выбросился на берег в странной деревне после кораблекрушения. "
            "Ваше путешествие начинается сейчас. Что вы делаете?\n\n"
            "Ваше здоровье: 100%"
        )
        
        # Send welcome message with main menu keyboard
        bot.send_message(
            message.chat.id,
            welcome_msg,
            reply_markup=create_main_menu_keyboard()
        )
        
        print(f"Started game for user: {message.from_user.username} (ID: {message.chat.id})")
        
    except Exception as e:
        print(f"Error in start_command: {e}")
        bot.reply_to(message, "Произошла ошибка. Попробуйте еще раз.")

@bot.message_handler(commands=['restart'])
def restart_command(message):
    """
    Handle the /restart command
    Resets player state and sends welcome message again
    """
    try:
        # Reset player state
        reset_player_state(message.chat.id)
        
        # Create restart message
        restart_msg = (
            "Игра перезапущена! 🔄\n\n"
            "Вы снова в загадочной деревне после кораблекрушения. Что вы делаете?\n\n"
            "Ваше здоровье: 100%"
        )
        
        # Send restart message with main menu keyboard
        bot.send_message(
            message.chat.id,
            restart_msg,
            reply_markup=create_main_menu_keyboard()
        )
        
        print(f"Restarted game for user: {message.from_user.username} (ID: {message.chat.id})")
        
    except Exception as e:
        print(f"Error in restart_command: {e}")
        bot.reply_to(message, "Произошла ошибка. Попробуйте еще раз.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """
    Handle all other messages that are not commands
    """
    try:
        bot.reply_to(message, "Пожалуйста, используйте кнопки для выбора.")
    except Exception as e:
        print(f"Error handling message: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """
    Main callback handler for all inline keyboard button presses
    """
    try:
        # Acknowledge the callback
        bot.answer_callback_query(call.id)
        
        # Get player state
        player_state = get_player_state(call.message.chat.id)
        
        # Update current scene based on callback data
        if call.data.startswith('choice_'):
            player_state['current_scene'] = call.data
        
        # Handle different callback actions
        if call.data == 'choice_forest':
            scene_forest(call)
        elif call.data == 'choice_castle':
            scene_castle(call)
        elif call.data == 'choice_village_head':
            scene_village_head(call)
        elif call.data == 'check_inventory':
            scene_check_inventory(call)
        elif call.data == 'main_menu':
            scene_main_menu(call)
        elif call.data == 'forest_path_continue':
            scene_forest_path_continue(call)
        elif call.data == 'forest_stream':
            scene_forest_stream(call)
        elif call.data == 'forest_berries':
            scene_forest_berries(call)
        elif call.data == 'castle_stairs':
            scene_castle_stairs(call)
        elif call.data == 'castle_hall_search':
            scene_castle_hall_search(call)
        elif call.data == 'castle_door':
            scene_castle_door(call)
        elif call.data == 'village_legends':
            scene_village_legends(call)
        elif call.data == 'village_advice':
            scene_village_advice(call)
        elif call.data == 'village_help':
            scene_village_help(call)
        elif call.data == 'puzzle_correct':
            scene_puzzle_correct(call)
        elif call.data == 'puzzle_wrong':
            scene_puzzle_wrong(call)
        elif call.data == 'battle_fight':
            scene_battle_fight(call)
        elif call.data == 'battle_run':
            scene_battle_run(call)
        else:
            # Unknown callback
            bot.edit_message_text(
                "Неизвестный выбор. Пожалуйста, вернитесь в главное меню.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=create_back_to_menu_keyboard()
            )
        
    except Exception as e:
        print(f"Error in callback handler: {e}")
        try:
            bot.answer_callback_query(call.id, "Произошла ошибка. Попробуйте еще раз.")
        except:
            pass

def scene_main_menu(call):
    """Return to main menu scene"""
    try:
        reset_player_state(call.message.chat.id)
        
        msg = (
            "Вы вернулись в главное меню! 🏡\n\n"
            "Добро пожаловать в Eldoria! Вы — смелый искатель приключений, который выбросился на берег в странной деревне после кораблекрушения. "
            "Ваше путешествие начинается сейчас. Что вы делаете?\n\n"
            "Ваше здоровье: 100%"
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_main_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_main_menu: {e}")

def scene_forest(call):
    """Forest scene - first level choice"""
    try:
        msg = (
            "Вы покидаете деревню и входите в густой лес. Деревья здесь высокие и мрачные, "
            "а между ними пробиваются солнечные лучи. Воздух наполнен ароматом мха и влажной листвы. "
            "Вы видите тропинку, ведущую вглубь леса, и слышите звуки животных.\n\n"
            "Что вы хотите сделать?"
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_scene_forest_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_forest: {e}")

def scene_forest_path_continue(call):
    """Continue along the forest path"""
    try:
        msg = (
            "Вы продолжаете идти по тропе, и вскоре замечаете странный камень с вырезанными символами. "
            "На камне написано: 'Только храбрец может пройти дальше. Ответь на загадку: "
            "Какое число является следующим в последовательности: 2, 3, 5, 11, 13, ?'\n\n"
            "Выберите правильный ответ:"
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_puzzle_solution_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_forest_path_continue: {e}")

def scene_forest_stream(call):
    """Go to the stream in the forest"""
    try:
        # Add a potion to inventory
        success = add_to_inventory(call.message.chat.id, 'Зелье здоровья')
        
        msg = (
            "Вы находите красивый ручей с кристально чистой водой. Вода светится мягким голубым светом. "
            "Рядом с ручьем вы замечаете бутылочку с таинственным зельем. "
            f"{'Вы добавляете зелье в инвентарь.' if success else 'У вас уже есть это зелье.'}\n\n"
            "Что вы делаете дальше?"
        )
        
        # Create new keyboard with different choices
        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Выпить зелье", callback_data='drink_potion')
        btn2 = types.InlineKeyboardButton("Продолжить путь", callback_data='continue_after_stream')
        btn3 = types.InlineKeyboardButton("Вернуться в деревню", callback_data='main_menu')
        
        keyboard.row(btn1)
        keyboard.row(btn2, btn3)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in scene_forest_stream: {e}")

def scene_forest_berries(call):
    """Look for berries in the forest"""
    try:
        # Add berries to inventory
        success = add_to_inventory(call.message.chat.id, 'Ягоды')
        
        msg = (
            "Вы находите куст со странными светящимися ягодами. Они имеют фиолетовый цвет и издают мягкий свет. "
            f"{'Вы добавляете ягоды в инвентарь.' if success else 'У вас уже есть эти ягоды.'}\n\n"
            "Вдалеке вы слышите рычание. Кажется, что-то движется в кустах..."
        )
        
        # Create new keyboard with encounter choices
        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Приготовиться к бою", callback_data='prepare_battle')
        btn2 = types.InlineKeyboardButton("Спрятаться", callback_data='hide_from_beast')
        btn3 = types.InlineKeyboardButton("Вернуться в деревню", callback_data='main_menu')
        
        keyboard.row(btn1, btn2)
        keyboard.row(btn3)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in scene_forest_berries: {e}")

def scene_castle(call):
    """Castle scene - first level choice"""
    try:
        msg = (
            "Вы подходите к руинам древнего замка. Стены покрыты мхом и лишайником, "
            "а башни частично разрушены временем. Ворота приоткрыты, и изнутри доносится странный шум. "
            "Вы чувствуете, что внутри может скрываться что-то ценное.\n\n"
            "Куда вы пойдете?"
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_scene_castle_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_castle: {e}")

def scene_castle_stairs(call):
    """Go up the stairs in the castle"""
    try:
        # Add a sword to inventory
        success = add_to_inventory(call.message.chat.id, 'Меч')
        
        msg = (
            "Вы поднимаетесь по витиеватой каменной лестнице. На стене висит старый меч в ножнах. "
            f"{'Вы берете меч и добавляете его в инвентарь.' if success else 'У вас уже есть меч.'}\n\n"
            "На верхней площадке вы видите дверь с символами. Из-за двери доносится таинственный свет."
        )
        
        # Create new keyboard with choices
        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Открыть дверь", callback_data='open_mystery_door')
        btn2 = types.InlineKeyboardButton("Осмотреть комнату", callback_data='inspect_room')
        btn3 = types.InlineKeyboardButton("Спуститься вниз", callback_data='go_downstairs')
        
        keyboard.row(btn1)
        keyboard.row(btn2, btn3)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in scene_castle_stairs: {e}")

def scene_castle_hall_search(call):
    """Search the hall in the castle"""
    try:
        # Add treasure to inventory
        success = add_to_inventory(call.message.chat.id, 'Сокровище')
        
        msg = (
            "Вы обыскиваете большой зал. На полу лежит пыльный ковер, а на стенах висят старые гобелены. "
            "В углу вы замечаете сундук с золотыми украшениями. "
            f"{'Вы открываете сундук и находите сокровище!' if success else 'Вы уже нашли сокровище ранее.'}\n\n"
            "Внезапно вы слышите шаги в коридоре. Кто-то идет!"
        )
        
        # Create new keyboard with choices
        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Спрятаться", callback_data='hide_in_castle')
        btn2 = types.InlineKeyboardButton("Пойти навстречу", callback_data='meet_guardian')
        btn3 = types.InlineKeyboardButton("Вернуться в деревню", callback_data='main_menu')
        
        keyboard.row(btn1, btn2)
        keyboard.row(btn3)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in scene_castle_hall_search: {e}")

def scene_castle_door(call):
    """Check the suspicious door in the castle"""
    try:
        msg = (
            "Вы подходите к подозрительной двери. Она выглядит новее остальных в замке, "
            "и на ней висит замок с символами. Когда вы прикасаетесь к двери, она медленно открывается, "
            "и вы видите комнату с алтарем посередине. На алтаре лежит свиток.\n\n"
            "Что вы делаете?"
        )
        
        # Create new keyboard with choices
        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Взять свиток", callback_data='take_scroll')
        btn2 = types.InlineKeyboardButton("Осмотреть алтарь", callback_data='examine_altar')
        btn3 = types.InlineKeyboardButton("Уйти", callback_data='leave_door')
        
        keyboard.row(btn1, btn2)
        keyboard.row(btn3)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in scene_castle_door: {e}")

def scene_village_head(call):
    """Village head scene - first level choice"""
    try:
        msg = (
            "Вы подходите к домику деревенского старосты. Это пожилой мужчина с седой бородой и добрыми глазами. "
            "Он сидит на лавочке перед домом и курит трубку. Увидев вас, он улыбается и машет рукой.\n\n"
            "'Ах, путешественник! Расскажи, что привело тебя в нашу деревню?'"
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_scene_village_head_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_village_head: {e}")

def scene_village_legends(call):
    """Ask about local legends"""
    try:
        msg = (
            "Староста задумчиво курит трубку: 'В наших краях ходят легенды о Древнем Хранителе, "
            "который охраняет сокровища в развалинах замка. Говорят, что тот, кто сможет решить его загадки, "
            "получит великую силу.'\n\n"
            "Он протягивает вам старую карту: 'Возьми, может пригодиться.'"
        )
        
        # Add map to inventory
        success = add_to_inventory(call.message.chat.id, 'Карта')
        
        # Create new keyboard with choices
        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Исследовать лес", callback_data='choice_forest')
        btn2 = types.InlineKeyboardButton("Посетить замок", callback_data='choice_castle')
        btn3 = types.InlineKeyboardButton("Поблагодарить старосту", callback_data='thank_village_head')
        
        keyboard.row(btn1, btn2)
        keyboard.row(btn3)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in scene_village_legends: {e}")

def scene_village_advice(call):
    """Ask for advice"""
    try:
        msg = (
            "Староста серьезно смотрит на вас: 'Если хочешь выжить в этих краях, запомни: "
            "в лесу опасайся светящихся ягод, в замке не доверяй дверям, которые слишком легко открываются, "
            "а в общении с духами всегда будь вежлив.'\n\n"
            "Он дает вам небольшой амулет: 'Этот талисман защитит тебя от злых духов.'"
        )
        
        # Add amulet to inventory
        success = add_to_inventory(call.message.chat.id, 'Амулет защиты')
        
        # Create new keyboard with choices
        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Исследовать местность", callback_data='explore_outskirts')
        btn2 = types.InlineKeyboardButton("Проверить инвентарь", callback_data='check_inventory')
        btn3 = types.InlineKeyboardButton("Поблагодарить старосту", callback_data='thank_village_head')
        
        keyboard.row(btn1)
        keyboard.row(btn2, btn3)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in scene_village_advice: {e}")

def scene_village_help(call):
    """Offer help to the village"""
    try:
        msg = (
            "Староста радостно улыбается: 'Ты готов помочь? В лесу завелась стая голодных волков, "
            "они стали нападать на скот. Если ты справишься с ними, весь урожай этого года будет твоим.'\n\n"
            "Вы соглашаетесь на задание и направляетесь в лес..."
        )
        
        # Create new keyboard with choices
        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Идти в лес", callback_data='go_to_wolves')
        btn2 = types.InlineKeyboardButton("Отказаться от задания", callback_data='decline_quest')
        
        keyboard.row(btn1, btn2)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in scene_village_help: {e}")

def scene_check_inventory(call):
    """Check player inventory"""
    try:
        player_state = get_player_state(call.message.chat.id)
        inventory_msg = get_inventory_message(player_state['inventory'])
        
        msg = f"{inventory_msg}\n\nЧто вы хотите сделать дальше?"
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_check_inventory: {e}")

def scene_puzzle_correct(call):
    """Correct answer to the puzzle"""
    try:
        # Add treasure to inventory
        success = add_to_inventory(call.message.chat.id, 'Ключ от сокровищницы')
        
        msg = (
            "Правильный ответ! Камень начинает светиться, и вы слышите щелчок. "
            f"Из земли под вами появляется ключ. {'Вы добавляете ключ в инвентарь.' if success else 'У вас уже есть этот ключ.'}\n\n"
            "Теперь вы можете открыть любую дверь в замке!"
        )
        
        # Create new keyboard with choices
        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Вернуться в деревню", callback_data='main_menu')
        btn2 = types.InlineKeyboardButton("Проверить инвентарь", callback_data='check_inventory')
        
        keyboard.row(btn1, btn2)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in scene_puzzle_correct: {e}")

def scene_puzzle_wrong(call):
    """Wrong answer to the puzzle"""
    try:
        msg = (
            "Неправильный ответ! Камень начинает вибрировать, и вы чувствуете, как земля под вами начинает дрожать. "
            "Вы спешите прочь от места, где стоял камень. Внезапно из-под земли вырастает стена из колючих кустов, "
            "блокирующая дальнейший путь по тропе."
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_puzzle_wrong: {e}")

def scene_battle_fight(call):
    """Fight in battle"""
    try:
        player_state = get_player_state(call.message.chat.id)
        
        # Check if player has a sword
        has_sword = 'Меч' in player_state['inventory']
        
        if has_sword:
            msg = (
                "Вы достаете меч и принимаете боевую стойку. Из кустов выходит огромный медведь! "
                "Вы уверенно атакуете, и после ожесточенной битвы побеждаете зверя. "
                "На его теле вы находите ценный амулет."
            )
            
            # Add bear_amulet to inventory
            success = add_to_inventory(call.message.chat.id, 'Амулет медведя')
        else:
            msg = (
                "Вы пытаетесь сражаться, но у вас нет оружия! Медведь оказывается сильнее, "
                "и вы получаете серьезные раны. С трудом убегая, вы возвращаетесь в деревню, чтобы восстановиться."
            )
            
            # Decrease health
            player_state['health'] = max(0, player_state['health'] - 30)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_battle_fight: {e}")

def scene_battle_run(call):
    """Run from battle"""
    try:
        msg = (
            "Вы быстро убегаете от зверя. К счастью, он не преследует вас дальше. "
            "Вы возвращаетесь в деревню, тяжело дыша, но целы и невредимы."
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_battle_run: {e}")

# Additional scenes for continuity
def scene_drink_potion(call):
    """Drink the potion found at the stream"""
    try:
        player_state = get_player_state(call.message.chat.id)
        
        # Increase health
        old_health = player_state['health']
        player_state['health'] = min(100, player_state['health'] + 20)
        health_increase = player_state['health'] - old_health
        
        msg = f"Вы выпиваете зелье. Ваше здоровье восстанавливается на {health_increase}%."
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_drink_potion: {e}")

def scene_continue_after_stream(call):
    """Continue journey after finding the stream"""
    try:
        msg = (
            "Вы продолжаете путь по лесу и вскоре находите заброшенную часовню. "
            "Внутри вы видите алтарь с таинственным светом. На алтаре лежит свиток с заклинанием."
        )
        
        # Add scroll to inventory
        success = add_to_inventory(call.message.chat.id, 'Свиток заклинаний')
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_continue_after_stream: {e}")

def scene_prepare_battle(call):
    """Prepare for battle with the beast"""
    try:
        msg = (
            "Вы готовитесь к бою. Из кустов выходит гигантский волк! Он оскалил зубы и готовится к атаке. "
            "Теперь вы должны принять решение: сражаться или бежать?"
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_battle_choice_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_prepare_battle: {e}")

def scene_hide_from_beast(call):
    """Hide from the beast"""
    try:
        msg = (
            "Вы быстро прячетесь за деревом. Зверь несколько минут ищет вас, но затем уходит. "
            "Вы благополучно возвращаетесь в деревню."
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_hide_from_beast: {e}")

def scene_open_mystery_door(call):
    """Open the mystery door in the castle"""
    try:
        player_state = get_player_state(call.message.chat.id)
        
        # Check if player has the key
        has_key = 'Ключ от сокровищницы' in player_state['inventory']
        
        if has_key:
            msg = (
                "Вы используете найденный ключ, и дверь открывается! За ней находится сокровищница, "
                "полная золота, драгоценных камней и магических артефактов. Вы нашли сокровища!"
            )
            
            # Add treasure chest to inventory
            success = add_to_inventory(call.message.chat.id, 'Сокровищница')
        else:
            msg = (
                "Дверь заперта, и вы не можете найти способ открыть её. Вы возвращаетесь обратно."
            )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_open_mystery_door: {e}")

def scene_inspect_room(call):
    """Inspect the room in the castle"""
    try:
        msg = (
            "Вы осматриваете комнату и находите старую книгу с заклинаниями. "
            "На обложке написано 'Тайны Древнего Замка'. Вы добавляете книгу в инвентарь."
        )
        
        # Add book to inventory
        success = add_to_inventory(call.message.chat.id, 'Книга заклинаний')
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_inspect_room: {e}")

def scene_go_downstairs(call):
    """Go downstairs in the castle"""
    try:
        msg = (
            "Вы спускаетесь по лестнице и попадаете в подземелье. Здесь темно и сыро. "
            "На стенах горят факелы, отбрасывающие зловещие тени. "
            "Вы слышите странные звуки из глубины подземелья."
        )
        
        # Create new keyboard with choices
        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Исследовать подземелье", callback_data='explore_dungeon')
        btn2 = types.InlineKeyboardButton("Вернуться наверх", callback_data='go_upstairs')
        
        keyboard.row(btn1, btn2)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in scene_go_downstairs: {e}")

def scene_hide_in_castle(call):
    """Hide in the castle when hearing footsteps"""
    try:
        msg = (
            "Вы быстро прячетесь за колонной. Проходит вооруженный стражник в старом доспехе. "
            "Он осматривается, но не замечает вас. После того как он уходит, вы выходите из укрытия."
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_hide_in_castle: {e}")

def scene_meet_guardian(call):
    """Meet the guardian in the castle"""
    try:
        msg = (
            "Вы решаете пойти навстречу. Перед вами появляется старый рыцарь в ржавом доспехе. "
            "Это Древний Хранитель, о котором говорил староста! Он говорит: "
            "'Ты проявил смелость, путешественник. Пройди испытание, и получишь награду.'"
        )
        
        # Create new keyboard with choices
        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Принять вызов", callback_data='accept_challenge')
        btn2 = types.InlineKeyboardButton("Отказаться", callback_data='refuse_challenge')
        
        keyboard.row(btn1, btn2)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in scene_meet_guardian: {e}")

def scene_take_scroll(call):
    """Take the scroll from the altar"""
    try:
        # Add scroll to inventory
        success = add_to_inventory(call.message.chat.id, 'Свиток древних знаний')
        
        msg = (
            f"Вы берете свиток. На нем написаны древние символы, значение которых вам пока непонятно. "
            f"{'Свиток добавлен в инвентарь.' if success else 'У вас уже есть этот свиток.'}"
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_take_scroll: {e}")

def scene_examine_altar(call):
    """Examine the altar"""
    try:
        msg = (
            "Вы внимательно осматриваете алтарь. Он сделан из черного камня с серебряными вставками. "
            "В центре находится круглое углубление, похоже, для какого-то артефакта. "
            "На боковой стороне вы замечаете надпись: 'Только истинный герой может активировать меня.'"
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_examine_altar: {e}")

def scene_leave_door(call):
    """Leave the mysterious door"""
    try:
        msg = (
            "Вы решаете не рисковать и покидаете комнату. Возвращаясь в замок, "
            "вы чувствуете, что могли упустить важную возможность."
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_leave_door: {e}")

def scene_thank_village_head(call):
    """Thank the village head"""
    try:
        msg = (
            "Староста тепло улыбается: 'Спасибо тебе, путешественник. Моя дверь всегда открыта для тебя. "
            "Если понадобится помощь, обращайся.'\n\n"
            "Вы чувствуете, что в деревне вас теперь принимают как своего."
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_thank_village_head: {e}")

def scene_explore_outskirts(call):
    """Explore outskirts after talking to village head"""
    try:
        msg = (
            "Вы исследуете окрестности деревни и находите старую руину с таинственными символами. "
            "Внутри вы видите алтарь, похожий на тот, что был в замке. "
            "Кажется, эти два места связаны между собой."
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_explore_outskirts: {e}")

def scene_go_to_wolves(call):
    """Go to fight wolves for the village quest"""
    try:
        msg = (
            "Вы отправляетесь в лес на поиски стаи волков. Вскоре вы находите их логово. "
            "Перед вами пятеро крупных волков, которые замечают вас и начинают рычать. "
            "Вам предстоит тяжелый бой..."
        )
        
        # Create new keyboard with battle choices
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_battle_choice_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_go_to_wolves: {e}")

def scene_decline_quest(call):
    """Decline the village quest"""
    try:
        msg = (
            "Вы вежливо отказываетесь от задания. Староста кивает: 'Я понимаю. "
            "Но помни, что деревня всегда нуждается в храбрых людях.'\n\n"
            "Вы возвращаетесь в главное меню."
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_decline_quest: {e}")

def scene_explore_dungeon(call):
    """Explore the dungeon"""
    try:
        msg = (
            "Вы исследуете подземелье и находите несколько комнат. В одной из них лежит сундук, "
            "в другой вы видите решетку, за которой слышится рычание. "
            "Третья комната полностью пуста, но на полу вы замечаете странные символы."
        )
        
        # Create new keyboard with choices
        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Открыть сундук", callback_data='open_dungeon_chest')
        btn2 = types.InlineKeyboardButton("Проверить решетку", callback_data='check_grate')
        btn3 = types.InlineKeyboardButton("Изучить символы", callback_data='study_symbols')
        
        keyboard.row(btn1)
        keyboard.row(btn2, btn3)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in scene_explore_dungeon: {e}")

def scene_go_upstairs(call):
    """Go upstairs from dungeon"""
    try:
        msg = (
            "Вы поднимаетесь обратно наверх. Попав в главный зал замка, "
            "вы чувствуете облегчение от покинутого мрачного подземелья."
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_go_upstairs: {e}")

def scene_accept_challenge(call):
    """Accept the guardian's challenge"""
    try:
        msg = (
            "Древний Хранитель улыбается: 'Хорошо! Вот твое испытание: реши мою загадку, "
            "и получишь величайшую награду.'\n\n"
            "Загадка: 'Я могу быть разбит, но никогда не падаю. Я могу быть задан, но никогда не болен. Что я?'"
        )
        
        # Create new keyboard with answer choices
        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Сердце", callback_data='challenge_wrong')
        btn2 = types.InlineKeyboardButton("Рекорд", callback_data='challenge_wrong')
        btn3 = types.InlineKeyboardButton("Обещание", callback_data='challenge_correct')
        
        keyboard.row(btn1, btn2, btn3)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in scene_accept_challenge: {e}")

def scene_refuse_challenge(call):
    """Refuse the guardian's challenge"""
    try:
        msg = (
            "Хранитель кивает: 'Ты выбрал безопасный путь, но возможно упустил великую возможность. "
            "Мир не ждет героев, что боятся рисковать.'\n\n"
            "Он исчезает в вихре теней, оставляя после себя лишь эхо смеха."
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_refuse_challenge: {e}")

def scene_open_dungeon_chest(call):
    """Open the dungeon chest"""
    try:
        # Add random treasure to inventory
        success = add_to_inventory(call.message.chat.id, 'Драгоценный камень')
        
        msg = (
            f"Вы открываете сундук и находите драгоценный камень, излучающий магический свет. "
            f"{'Камень добавлен в инвентарь.' if success else 'У вас уже есть этот камень.'}"
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_open_dungeon_chest: {e}")

def scene_check_grate(call):
    """Check the grate in dungeon"""
    try:
        msg = (
            "Вы подходите к решетке и видите за ней большую клетку. "
            "Внутри сидит древний дракон, но он выглядит скорее усталым, чем злым. "
            "Он говорит: 'Путешественник, если ты освободишь меня, я дам тебе мудрость веков.'"
        )
        
        # Create new keyboard with choices
        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Освободить дракона", callback_data='free_dragon')
        btn2 = types.InlineKeyboardButton("Уйти", callback_data='leave_grate')
        
        keyboard.row(btn1, btn2)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in scene_check_grate: {e}")

def scene_study_symbols(call):
    """Study the symbols in dungeon"""
    try:
        msg = (
            "Вы внимательно изучаете символы на полу. Они образуют магический круг. "
            "Похоже, когда-то здесь происходили важные ритуалы. "
            "Вы запоминаете расположение символов, возможно, это пригодится позже."
        )
        
        # Add knowledge to inventory
        success = add_to_inventory(call.message.chat.id, 'Знания о символах')
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_study_symbols: {e}")

def scene_free_dragon(call):
    """Free the dragon"""
    try:
        msg = (
            "Вы находите механизм и открываете клетку. Дракон медленно поднимается и благодарит вас: "
            "'Спасибо, храбрый путник. Я дарую тебе часть своей мудрости.'\n\n"
            "Вы получаете артефакт древней магии!"
        )
        
        # Add dragon artifact to inventory
        success = add_to_inventory(call.message.chat.id, 'Артефакт дракона')
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_free_dragon: {e}")

def scene_leave_grate(call):
    """Leave the grate in dungeon"""
    try:
        msg = (
            "Вы решаете не связываться с драконом и покидаете эту часть подземелья. "
            "За спиной слышится тяжелый вздох, но вы не оглядываетесь."
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_leave_grate: {e}")

def scene_challenge_correct(call):
    """Correct answer to the guardian's challenge"""
    try:
        msg = (
            "Хранитель улыбается: 'Правильно! Обещание можно разбить, но нельзя упасть или заболеть. "
            "Ты прошел испытание достойно!'\n\n"
            "Он передает вам древний артефакт: 'Это Сердце Эльдории. Оно защитит тебя в пути.'"
        )
        
        # Add heart artifact to inventory
        success = add_to_inventory(call.message.chat.id, 'Сердце Эльдории')
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_challenge_correct: {e}")

def scene_challenge_wrong(call):
    """Wrong answer to the guardian's challenge"""
    try:
        msg = (
            "Хранитель качает головой: 'Неправильно, путешественник. Ты не готов к великим испытаниям.'\n\n"
            "Он исчезает, оставляя вас одного в пустой комнате."
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in scene_challenge_wrong: {e}")

def main():
    """
    Main function to run the bot
    Loads player data and starts polling
    """
    print("Starting Telegram RPG Adventure Bot...")
    
    print(f"Bot is ready! Token configured: {'Yes' if BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else 'No (placeholder)'}")
    print("Replace 'YOUR_BOT_TOKEN_HERE' with your actual bot token from @BotFather")
    
    # Start the bot with infinity polling
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error running bot: {e}")
    finally:
        print("Bot stopped.")

if __name__ == '__main__':
    main()