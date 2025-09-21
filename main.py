import os
import io
import time
import json
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, CallbackContext
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from moviepy import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from dotenv import load_dotenv


load_dotenv()

CACHE_DIR = 'cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

async def start(update: Update, context: CallbackContext) -> None:
    menu = load_menu()
    reply_keyboard = menu['keyboard']
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    instructions = """
    به ربات تلگرامی خوش آمدید!

    دستورالعمل‌ها:
    1. برای ویرایش تصویر، گزینه 'ویرایش تصویر' را انتخاب کنید.
    2. برای ویرایش ویدئو، گزینه 'ویرایش ویدئو' را انتخاب کنید.
    3. برای بروزرسانی ربات، گزینه 'بروزرسانی ربات' را انتخاب کنید.

    لطفا یکی از گزینه‌های زیر را انتخاب کنید.
    """

    await update.message.reply_text(instructions, reply_markup=markup)

async def update_bot(update: Update, context: CallbackContext) -> None:
    menu = load_menu()
    reply_keyboard = menu['keyboard']
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    await update.message.reply_text('ربات به‌روزرسانی شد!', reply_markup=markup)
    await start(update, context)

async def edit_image(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('لطفا تصویر مورد نظر خود را ارسال کنید:')
    context.user_data['awaiting_image'] = True

async def handle_image(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('awaiting_image'):
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        image = Image.open(io.BytesIO(photo_bytes))

        # دسته بندی و دو ستونه کردن دکمه‌ها با خطوط جداکننده
        keyboard = [
            # Filters
            [InlineKeyboardButton(" فیلتر ها ", callback_data='none')],
            [InlineKeyboardButton("Blur", callback_data='BLUR'),
             InlineKeyboardButton("Contour", callback_data='CONTOUR')],
            [InlineKeyboardButton("Detail", callback_data='DETAIL'),
             InlineKeyboardButton("Emboss", callback_data='EMBOSS')],
            [InlineKeyboardButton("Sharpen", callback_data='SHARPEN'),
             InlineKeyboardButton("Grayscale", callback_data='GRAYSCALE')],
            [InlineKeyboardButton("Sepia", callback_data='SEPIA'),
             InlineKeyboardButton("Negative", callback_data='NEGATIVE')],
            [InlineKeyboardButton("Vintage", callback_data='VINTAGE')],

            [InlineKeyboardButton("----------------------------------", callback_data='none')],
            [InlineKeyboardButton(" تغییرات کیفیت ", callback_data='none')],
            # Image Quality Enhancement
            [InlineKeyboardButton("Brightness High", callback_data='BRIGHTNESS_H'),
             InlineKeyboardButton("Brightness Low", callback_data='BRIGHTNESS_L')],
            [InlineKeyboardButton("Contrast High", callback_data='CONTRAST_H'),
             InlineKeyboardButton("Contrast Low", callback_data='CONTRAST_L')],
            [InlineKeyboardButton("Enhance Quality High", callback_data='ENHANCE_QUALITY_H'),
             InlineKeyboardButton("Enhance Quality Medium", callback_data='ENHANCE_QUALITY_M')],
            [InlineKeyboardButton("Color Adjust High", callback_data='COLOR_ADJUST_H'),
             InlineKeyboardButton("Color Adjust Low", callback_data='COLOR_ADJUST_L')],

            [InlineKeyboardButton("----------------------------------", callback_data='none')],
            [InlineKeyboardButton(" چرخاندن تصاویر ", callback_data='none')],
            # Rotate Image
            [InlineKeyboardButton("Rotate 90°", callback_data='ROTATE_N'),
             InlineKeyboardButton("Rotate 180°", callback_data='ROTATE_S')],
            [InlineKeyboardButton("Rotate 270°", callback_data='ROTATE_D')],

            [InlineKeyboardButton("----------------------------------", callback_data='none')],
            [InlineKeyboardButton(" سایز تصاویر ", callback_data='none')],
            # Resize
            [InlineKeyboardButton("Resize Small", callback_data='RESIZE_S'),
             InlineKeyboardButton("Resize Large", callback_data='RESIZE_L')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data['image'] = image
        await update.message.reply_text('Please choose an option:', reply_markup=reply_markup)
        context.user_data['awaiting_image'] = False

async def apply_filter(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    filter_type = query.data
    image = context.user_data.get('image')
    print(f"Applying filter: {filter_type}")

    if image:
        if filter_type == 'BLUR':
            filtered_image = image.filter(ImageFilter.BLUR)
        elif filter_type == 'CONTOUR':
            filtered_image = image.filter(ImageFilter.CONTOUR)
        elif filter_type == 'DETAIL':
            filtered_image = image.filter(ImageFilter.DETAIL)
        elif filter_type == 'EMBOSS':
            filtered_image = image.filter(ImageFilter.EMBOSS)
        elif filter_type == 'SHARPEN':
            filtered_image = image.filter(ImageFilter.SHARPEN)
        elif filter_type == 'RESIZE_S':
            filtered_image = image.resize((image.width // 2, image.height // 2))
        elif filter_type == 'RESIZE_L':
            filtered_image = image.resize((image.width * 2, image.height * 2))
        elif filter_type == 'ROTATE_N':
            filtered_image = image.rotate(90, expand=True)
        elif filter_type == 'ROTATE_S':
            filtered_image = image.rotate(180, expand=True)
        elif filter_type == 'ROTATE_D':
            filtered_image = image.rotate(270, expand=True)
        elif filter_type == 'BRIGHTNESS_H':
            enhancer = ImageEnhance.Brightness(image)
            filtered_image = enhancer.enhance(1.5)
        elif filter_type == 'BRIGHTNESS_L':
            enhancer = ImageEnhance.Brightness(image)
            filtered_image = enhancer.enhance(0.5)
        elif filter_type == 'CONTRAST_H':
            enhancer = ImageEnhance.Contrast(image)
            filtered_image = enhancer.enhance(1.7)
        elif filter_type == 'CONTRAST_L':
            enhancer = ImageEnhance.Contrast(image)
            filtered_image = enhancer.enhance(0.4)
        elif filter_type == 'ENHANCE_QUALITY_H':
            enhancer = ImageEnhance.Sharpness(image)
            filtered_image = enhancer.enhance(2.8)
        elif filter_type == 'ENHANCE_QUALITY_M':
            enhancer = ImageEnhance.Sharpness(image)
            filtered_image = enhancer.enhance(1.8)
        elif filter_type == 'GRAYSCALE':
            filtered_image = image.convert('L')
        elif filter_type == 'COLOR_ADJUST_H':
            enhancer = ImageEnhance.Color(image)
            filtered_image = enhancer.enhance(2)
        elif filter_type == 'COLOR_ADJUST_L':
            enhancer = ImageEnhance.Color(image)
            filtered_image = enhancer.enhance(0.4)
        elif filter_type == 'SEPIA':
            try:
                print("Applying Sepia filter...")
                sepia_image = image.convert("RGB")
                width, height = sepia_image.size
                pixels = sepia_image.load()
                for py in range(height):
                    for px in range(width):
                        r, g, b = sepia_image.getpixel((px, py))

                        tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                        tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                        tb = int(0.272 * r + 0.534 * g + 0.131 * b)

                        pixels[px, py] = (min(tr, 255), min(tg, 255), min(tb, 255))

                filtered_image = sepia_image
                print("Sepia filter applied successfully.")
            except Exception as e:
                print(f"Error in Sepia filter: {e}")
        elif filter_type == 'NEGATIVE':
            try:
                print("Applying Negative filter...")
                filtered_image = ImageOps.invert(image.convert("RGB"))
                print("Negative filter applied successfully.")
            except Exception as e:
                print(f"Error in Negative filter: {e}")
        elif filter_type == 'VINTAGE':
            try:
                print("Applying Vintage filter...")
                vintage_image = image.convert("RGB")
                enhancer = ImageEnhance.Color(vintage_image)
                filtered_image = enhancer.enhance(0.2)
                print("Vintage filter applied successfully.")
            except Exception as e:
                print(f"Error in Vintage filter: {e}")
        else:
            await query.message.reply_text('گزینه انتخابی نامشخص است.')
            return

        byte_arr = io.BytesIO()
        filtered_image.save(byte_arr, format='PNG')
        byte_arr.seek(0)

        await query.message.reply_photo(photo=byte_arr, caption=f'This image is edited with {filter_type} option.')

async def edit_video(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Please send the video you want to edit:')
    context.user_data['awaiting_video'] = True

async def handle_video(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('awaiting_video'):
        video = update.message.video
        video_file = await video.get_file()
        video_path = os.path.join(CACHE_DIR, f"{video.file_id}.mp4")
        await video_file.download_to_drive(video_path)

        # Create a keyboard with video editing options
        keyboard = [
            [InlineKeyboardButton("Convert to MP3", callback_data='CONVERT_MP3')],
            [InlineKeyboardButton("Trim Video", callback_data='TRIM_VIDEO')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data['video_path'] = video_path
        await update.message.reply_text('Please choose an option:', reply_markup=reply_markup)
        context.user_data['awaiting_video'] = False

async def apply_video_edit(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    edit_type = query.data
    video_path = context.user_data.get('video_path')

    if video_path:
        if edit_type == 'CONVERT_MP3':
            video = VideoFileClip(video_path)
            audio_path = video_path.replace('.mp4', '.mp3')
            video.audio.write_audiofile(audio_path)
            await query.message.reply_audio(audio=open(audio_path, 'rb'), caption='Here is your MP3 file.')
            os.remove(audio_path)
        elif edit_type == 'TRIM_VIDEO':
            await query.message.reply_text(
                'Please enter the start and end time for trimming (e.g., 00:00:10-00:00:20):')
            context.user_data['awaiting_trim'] = True
        else:
            await query.message.reply_text('Unknown option selected.')

async def handle_trim_vc(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('awaiting_trim'):
        times = update.message.text.split('-')
        if len(times) != 2:
            await update.message.reply_text(
                'فرمت نادرست است. لطفا زمان شروع و پایان را به فرمت 00:00:10-00:00:20 وارد کنید.')
            return

        start_time = times[0]
        end_time = times[1]
        video_path = context.user_data.get('video_path')

        if video_path:
            try:
                video = VideoFileClip(video_path)
                duration = video.duration
                start_time_secs = sum(x * int(t) for x, t in zip([3600, 60, 1], start_time.split(":")))
                end_time_secs = sum(x * int(t) for x, t in zip([3600, 60, 1], end_time.split(":")))

                if start_time_secs >= duration or end_time_secs > duration:
                    await update.message.reply_text(
                        'زمان وارد شده بیشتر از زمان ویدئو می‌باشد. لطفا زمان‌های معتبر وارد کنید.')
                    video.close()
                    return

                trimmed_path = video_path.replace('.mp4', '_trimmed.mp4')
                video.close()
                ffmpeg_extract_subclip(video_path, start_time_secs, end_time_secs, outputfile=trimmed_path)

                time.sleep(1)  # اضافه کردن تأخیر برای اطمینان از آزاد شدن فایل

                await update.message.reply_video(video=open(trimmed_path, 'rb'), caption='این ویدئوی برید شده شماست.')
                os.remove(trimmed_path)
                context.user_data['awaiting_trim'] = False

                os.remove(video_path)
                await update.message.reply_text('عملیات بریدن ویدئو با موفقیت انجام شد.')
            except Exception as e:
                await update.message.reply_text(f'خطایی رخ داد: {e}')
                print(f'Error trimming video: {e}')

def load_menu():
    with open('menu_config.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def main() -> None:
    token = "your token address"

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex('^(بروزرسانی ربات)$'), update_bot))
    application.add_handler(MessageHandler(filters.Regex('^(ویرایش تصویر)$'), edit_image))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(CallbackQueryHandler(apply_filter,
                                                 pattern='^(BLUR|CONTOUR|DETAIL|EMBOSS'
                                                         '|SHARPEN|RESIZE_S|RESIZE_L|ROTATE_N'
                                                         '|ROTATE_S|ROTATE_D|BRIGHTNESS_H'
                                                         '|BRIGHTNESS_L|CONTRAST_H|CONTRAST_L'
                                                         '|ENHANCE_QUALITY_H|ENHANCE_QUALITY_M'
                                                         '|GRAYSCALE|COLOR_ADJUST_H|COLOR_ADJUST_L'
                                                         '|SEPIA|NEGATIVE|VINTAGE)$'))

    application.add_handler(MessageHandler(filters.Regex('^(ویرایش ویدئو)$'), edit_video))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(CallbackQueryHandler(apply_video_edit, pattern='^(CONVERT_MP3|TRIM_VIDEO)$'))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_trim_vc))

    application.run_polling()


if __name__ == '__main__':
    main()
