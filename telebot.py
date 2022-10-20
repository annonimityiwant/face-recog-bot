import telegram
from telegram.ext import ContextTypes
import configparser
from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.filters import Filters
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from io import BytesIO
from insightface.app import FaceAnalysis
import numpy as np
import cv2
import os
import faiss_ops
from sqlitedict import SqliteDict

config = configparser.ConfigParser()
config.read('config.conf')
my_password = config['telegrambot']['password']
bot_token = config['telegrambot']['bot_token']

need_init = True

index_path = 'index.p'  # path for faiss index , the vector db path used for vector searchs
db = SqliteDict("bot.sqlite", tablename="message_index", autocommit=True)  # db for saving faceid codes for each vector
db_code_msid = SqliteDict("bot.sqlite", tablename="code_message_id", autocommit=True)  # not used now

my_channel_id = None

app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

updater = Updater(bot_token,
                  use_context=True)

EXPECT_BUTTON, START_REPORT, START_QUERY, EXPECT_IMAGE, EXPECT_INFO, EXPECT_LOCATION, EXPECT_IMAGE_QUERY, CONTINUE_REPORT, ADD_TO_OLD_REPORT, GET_PASS, GET_CHANNEL = range(
    11)

if os.path.isfile(index_path):
    index = faiss_ops.load_index(index_path)
    print('index loaded from disc')
else:
    index = faiss_ops.create_index(512)


def start(update: Update, context: CallbackContext) -> None:
    """Sends a message with three inline buttons attached."""
    global need_init
    if need_init:
        keyboard = [
            [
                InlineKeyboardButton("گزارش", callback_data='report_init'),
                InlineKeyboardButton("استعلام", callback_data='query_init'),
                InlineKeyboardButton("راه اندازی", callback_data='initiation'),
            ],

        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("گزارش", callback_data='report_init'),
                InlineKeyboardButton("استعلام", callback_data='query_init'),

            ],

        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("به ربات صورت یاب خوش آمدید.\n"

                              , reply_markup=reply_markup)

    return EXPECT_BUTTON


def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""

    query = update.callback_query
    query_data = query.data
    if query_data == 'report_init':
        query.edit_message_text("لطفا فقط چهره شخص مورد نظر را ارسال کنید")
        return EXPECT_IMAGE
    elif query_data == 'query_init':
        query.edit_message_text("لطفا فقط چهره شخص مورد نظر را ارسال کنید")
        return EXPECT_IMAGE_QUERY
    elif query_data == 'same_person':
        query.edit_message_text(
            'لطفا هر اطلاعاتی راحع به این شخص دارید برای مااسال کنید. لطفا تمام توضیحات و عکس ها و فیلم ها را به صورت یک آلبوم بفرستید.'

        )
        return ADD_TO_OLD_REPORT
    elif query_data == 'new_person':
        query.edit_message_text(
            'لطفا هر اطلاعاتی راحع به این شخص دارید برای مااسال کنید. لطفا تمام توضیحات و عکس ها و فیلم ها را به صورت یک آلبوم بفرستید.'

        )

        embedding = context.user_data['embedding']

        idx = faiss_ops.add_2_indx(index, embedding)

        db[str(idx)] = {"code": str(idx)}

        context.user_data['idx'] = idx

        context.bot.send_message(chat_id=context.user_data['report_image_chat_id'], text='received image')
        context.bot.send_message(chat_id=context.user_data['report_image_chat_id'],
                                 text='لطفا هر اطلاعاتی راحع به این شخص دارید برای مااسال کنید. لطفا تمام توضیحات و عکس ها و فیلم ها را به صورت یک آلبوم بفرستید.'
                                 )

        faiss_ops.save_index(index, index_path)

        return EXPECT_INFO

    elif query_data == 'initiation':
        query.edit_message_text("لطفا کلمه عبور را وارد کنید، این راه اندازی برای شناسایی کانال گزارش ها است.")
        return GET_PASS


def get_password(update: Update, context: CallbackContext):
    password = update.message.text
    if password == my_password:
        update.message.reply_text(
            text='لطفا یک پیغام از کانالی که می خواهید گزارش ها در آن انتشار یابند را به این ربات فوروارد کنید. این ربات باید حتما در آن کانال به عنوان ادمین اصافه شده باشد.')

        return GET_CHANNEL
    else:
        update.message.reply_text(
            text='رمز اشتباه است، دوباره تلاش کنید. /start')


def get_channel(update: Update, context: CallbackContext):
    global my_channel_id
    global need_init
    try:
        message = update.message
        my_channel_id = message['forward_from_chat']['id']
        update.message.reply_text(
            text='راه اندازی با موفقیت انجام شد /start')
        need_init = False
    except:
        update.message.reply_text(
            text=' دوباره تلاش کنید. /start')

    return ConversationHandler.END


def get_image_report(update: Update, context: CallbackContext):
    file = context.bot.get_file(update.message.photo[-1].file_id)
    f = BytesIO(file.download_as_bytearray())
    img_array = np.asarray(bytearray(f.read()), dtype=np.uint8)
    img = cv2.imdecode(img_array, 1)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    faces = app.get(img)
    if len(faces) < 1:
        update.message.reply_text(text='در این عکس هیچ صورتی یافت نشد لطفا، عکس واضح تر ارسال کنید.')
        return ConversationHandler.END
    # send photo edited

    rimg = app.draw_on(img, faces)
    is_success, buffer = cv2.imencode(".png", cv2.cvtColor(rimg, cv2.COLOR_RGB2BGR))
    g = BytesIO(buffer)
    update.message.reply_photo(g)
    g.close()
    # end send
    # search if someone similar exists
    if index.ntotal > 1:
        indexes, scores, vecs, similarities = faiss_ops.search(index, faces[0]['embedding'])
        context.user_data['embedding'] = faces[0]['embedding']

        context.user_data['report_image_message_id'] = update.message.message_id
        context.user_data['report_image_chat_id'] = update.message.chat_id

        if len(similarities) > 0:
            if similarities[0] > 0.2:

                code = db[str(indexes[0])]['code']
                context.user_data['idx'] = code
                text = 'یک چهره با شباهت {} درصد در میان چهره های ارسالی پیدا شد، کد پیام مورد نطر در کانال #faceid{} است. آیا تصویر ارسال شده با شخصی که می خواهید گزارش دهید مربوط به یک شخص است ؟'.format(
                    str(similarities[0] * 100), str(code))

                keyboard = [
                    [
                        InlineKeyboardButton("بله", callback_data='same_person'),
                        InlineKeyboardButton("خیر، می خواهم برای یک شخص جدید اطلاع بدهم", callback_data='new_person'),
                    ],

                ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                context.bot.send_message(chat_id=update.message.chat_id, text=text, reply_markup=reply_markup)
                f.close()
                return EXPECT_BUTTON
            else:

                idx = faiss_ops.add_2_indx(index, faces[0]['embedding'])

                db[str(idx)] = {"code": str(idx)}

                context.user_data['idx'] = idx

                context.bot.send_message(chat_id=update.message.chat_id, text='received image')
                context.bot.send_message(chat_id=update.message.chat_id,
                                         text='لطفا هر اطلاعاتی راحع به این شخص دارید برای مااسال کنید. لطفا تمام توضیحات و عکس ها و فیلم ها را به صورت یک آلبوم بفرستید.'

                                         )
                f.close()

                faiss_ops.save_index(index, index_path)
                return EXPECT_INFO
        else:

            idx = faiss_ops.add_2_indx(index, faces[0]['embedding'])

            db[str(idx)] = {"code": str(idx)}

            context.user_data['report_image_message_id'] = update.message.message_id
            context.user_data['report_image_chat_id'] = update.message.chat_id
            context.user_data['idx'] = idx

            context.bot.send_message(chat_id=update.message.chat_id, text='received image')
            context.bot.send_message(chat_id=update.message.chat_id,
                                     text='لطفا هر اطلاعاتی راحع به این شخص دارید برای مااسال کنید. لطفا تمام توضیحات و عکس ها و فیلم ها را به صورت یک آلبوم بفرستید.'

                                     )
            f.close()

            faiss_ops.save_index(index, index_path)
            return EXPECT_INFO
    else:

        idx = faiss_ops.add_2_indx(index, faces[0]['embedding'])

        db[str(idx)] = {"code": str(idx)}

        context.user_data['report_image_message_id'] = update.message.message_id
        context.user_data['report_image_chat_id'] = update.message.chat_id
        context.user_data['idx'] = idx

        context.bot.send_message(chat_id=update.message.chat_id, text='received image')
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='لطفا هر اطلاعاتی راحع به این شخص دارید برای مااسال کنید. لطفا تمام توضیحات و عکس ها و فیلم ها را به صورت یک آلبوم بفرستید.'

                                 )
        f.close()

        faiss_ops.save_index(index, index_path)
        return EXPECT_INFO


def add_2_old_report(update: Update, context: CallbackContext):
    global my_channel_id
    info = update.message

    text = 'code: #faceid' + str(context.user_data['idx'])
    context.bot.send_message(chat_id=my_channel_id,
                             text=text)
    context.bot.copy_message(chat_id=my_channel_id, from_chat_id=context.user_data['report_image_chat_id'],
                             message_id=context.user_data['report_image_message_id'], )
    context.bot.copy_message(chat_id=my_channel_id, from_chat_id=update.message.chat_id, message_id=info.message_id, )
    context.user_data['report_info_message_id'] = update.message.message_id
    context.bot.send_message(chat_id=update.message.chat_id,
                             text='از اطلاع رسانی شما ممنونیم، برای شروع دوباره /start را بزنید')
    return ConversationHandler.END


def get_image_query(update: Update, context: CallbackContext):
    file = context.bot.get_file(update.message.photo[-1].file_id)
    f = BytesIO(file.download_as_bytearray())
    img_array = np.asarray(bytearray(f.read()), dtype=np.uint8)
    img = cv2.imdecode(img_array, 1)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    faces = app.get(img)
    indexes, scores, vecs, similarities = faiss_ops.search(index, faces[0]['embedding'])
    code = db[str(indexes[0])]['code']
    intensity = 'کم'
    if similarities[0] < 0.3:
        intensity = 'کم'
    elif similarities[0] < 0.5:
        intensity = 'متوسط'
    elif similarities[0] < 0.7:
        intensity = 'زیاد'
    else:
        intensity = 'خیلی زیاد'

    text = 'یک چهره با شباهت {} ({} درصد) در میان چهره های ارسالی پیدا شد، کد پیام مورد نطر در کانال #faceid{} است. این ربات دارای خطا می باشد، قضاوت نهایی با شما است.'.format(
        intensity, str(round(similarities[0] * 100, 2)), str(code))

    context.bot.send_message(chat_id=update.message.chat_id, text=text)
    context.bot.send_message(chat_id=update.message.chat_id,
                             text='از اطلاع رسانی شما ممنونیم، برای شروع دوباره /start را بزنید')

    return ConversationHandler.END


def get_info_2_old(update: Update, context: CallbackContext):
    global my_channel_id
    info = update.message

    text = 'code: #faceid' + str(context.user_data['idx'])
    context.bot.send_message(chat_id=my_channel_id,
                             text=text)
    context.bot.copy_message(chat_id=my_channel_id, from_chat_id=update.message.chat_id, message_id=info.message_id, )
    context.user_data['report_info_message_id'] = update.message.message_id
    context.bot.send_message(chat_id=update.message.chat_id,
                             text='از اطلاع رسانی شما ممنونیم، برای شروع دوباره /start را بزنید')
    return ConversationHandler.END


def get_info(update: Update, context: CallbackContext):
    global my_channel_id
    info = update.message

    text = 'code: #faceid' + str(context.user_data['idx'])

    context.bot.send_message(chat_id=my_channel_id,
                             text=text)
    context.bot.copy_message(chat_id=my_channel_id, from_chat_id=context.user_data['report_image_chat_id'],
                             message_id=context.user_data['report_image_message_id'], )
    context.bot.copy_message(chat_id=my_channel_id, from_chat_id=update.message.chat_id, message_id=info.message_id, )
    context.user_data['report_info_message_id'] = update.message.message_id
    context.bot.send_message(chat_id=update.message.chat_id,
                             text='از اطلاع رسانی شما ممنونیم، برای شروع دوباره /start را بزنید')
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text(
        'برای شروع دوباره /start را بزنید')
    return ConversationHandler.END


def help_command(update: Update, context: CallbackContext) -> None:
    """Displays info on how to use the bot."""
    update.message.reply_text("Use /start to test this bot.")


updater.dispatcher.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            EXPECT_BUTTON: [CallbackQueryHandler(button)],
            EXPECT_IMAGE: [MessageHandler(Filters.photo, get_image_report)],
            EXPECT_INFO: [MessageHandler(Filters.all, get_info)],
            EXPECT_IMAGE_QUERY: [MessageHandler(Filters.photo, get_image_query)],
            GET_PASS: [MessageHandler(Filters.text, get_password)],
            GET_CHANNEL: [MessageHandler(Filters.text, get_channel)],
            # CONTINUE_REPORT: [MessageHandler(Filters.photo, continue_report)],
            ADD_TO_OLD_REPORT: [MessageHandler(Filters.all, get_info_2_old)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
)

updater.dispatcher.logger.addFilter(
    (lambda s: not s.msg.endswith('A TelegramError was raised while processing the Update')))
updater.start_polling()
