"""Translation strings for English and Persian."""

from __future__ import annotations

from typing import Any

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English 🇬🇧",
    "fa": "فارسی 🇮🇷",
}

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "welcome": (
            "👋 Welcome to <b>SkyPing</b>!\n\n"
            "I can show current weather, save your favourite cities, "
            "and send a daily forecast to this chat.\n\n"
            "<b>Quick tips</b>\n"
            "• Send a city name, or use /weather &lt;city&gt;\n"
            "• /add &lt;city&gt; to save it\n"
            "• /list · /remove · /all for your cities\n"
            "• /subscribe &lt;city&gt; for a daily post\n"
            "• /forecast [1-7] &lt;city&gt; for multi-day outlook\n"
            "• /alerts on|off — rain alerts for saved cities\n"
            "• Type @SkyPingBot &lt;city&gt; in any chat (inline)\n"
            "• /language to switch language\n\n"
            "Here is the weather for the default city:"
        ),
        "help_commands": "Use the menu or type a command to get started.",
        "choose_language": "🌐 Choose your language:",
        "language_set": "✅ Language set to <b>{language}</b>.",
        "searching": "🔎 Searching for <b>{query}</b>…",
        "no_results": "😕 No cities found for <b>{query}</b>. Try another spelling.",
        "api_error": "⚠️ Weather service is temporarily unavailable. Please try again later.",
        "timeout": "⏳ The request timed out. Please try again.",
        "select_city": "Select a city:",
        "expired_selection": "⌛ This selection expired. Please search again.",
        "weather_header": "📍 <b>{place}</b>",
        "units_set": "✅ Units set to <b>{units}</b>.",
        "units_invalid": "Usage: /units metric|imperial",
        "city_added": "✅ Added <b>{place}</b> to your list.",
        "city_already": "ℹ️ <b>{place}</b> is already in your list.",
        "city_limit": "⚠️ Limit reached ({max} cities). Remove one with /remove first.",
        "city_removed": "🗑 Removed <b>{place}</b>.",
        "no_cities": "📭 You have no saved cities yet. Use /add &lt;city&gt;.",
        "list_title": "🏙 Your saved cities — tap one for weather:",
        "remove_title": "🗑 Tap a city to remove it:",
        "all_title": "🌤 Weather for all your cities:",
        "subscribe_ok": "✅ Subscribed this chat to daily weather for <b>{place}</b>.",
        "subscribe_already": "ℹ️ Already subscribed to <b>{place}</b>.",
        "unsubscribe_title": "🔕 Tap a city to unsubscribe:",
        "unsubscribed": "✅ Unsubscribed from <b>{place}</b>.",
        "no_subscriptions": "📭 No active subscriptions. Use /subscribe &lt;city&gt;.",
        "settime_usage": "Usage: /settime HH:MM  (24-hour, e.g. 07:30)",
        "settime_ok": "✅ Daily send time set to <b>{time}</b> ({tz}).",
        "settimezone_usage": "Usage: /settimezone &lt;IANA tz&gt;  e.g. Asia/Tehran",
        "settimezone_invalid": "❌ Unknown timezone <b>{tz}</b>. Use an IANA name like Europe/London.",
        "settimezone_ok": "✅ Timezone set to <b>{tz}</b>.",
        "admin_only": "🔒 Only group admins can change subscriptions here.",
        "need_city_arg": "Please provide a city name. Example: <code>{example}</code>",
        "condition": "Condition",
        "temperature": "Temperature",
        "feels_like": "Feels like",
        "today_range": "Today",
        "wind": "Wind",
        "humidity": "Humidity",
        "precip": "Precip. chance",
        "wmo_0": "Clear sky",
        "wmo_1": "Mainly clear",
        "wmo_2": "Partly cloudy",
        "wmo_3": "Overcast",
        "wmo_45": "Fog",
        "wmo_48": "Depositing rime fog",
        "wmo_51": "Light drizzle",
        "wmo_53": "Moderate drizzle",
        "wmo_55": "Dense drizzle",
        "wmo_56": "Light freezing drizzle",
        "wmo_57": "Dense freezing drizzle",
        "wmo_61": "Slight rain",
        "wmo_63": "Moderate rain",
        "wmo_65": "Heavy rain",
        "wmo_66": "Light freezing rain",
        "wmo_67": "Heavy freezing rain",
        "wmo_71": "Slight snow",
        "wmo_73": "Moderate snow",
        "wmo_75": "Heavy snow",
        "wmo_77": "Snow grains",
        "wmo_80": "Slight rain showers",
        "wmo_81": "Moderate rain showers",
        "wmo_82": "Violent rain showers",
        "wmo_85": "Slight snow showers",
        "wmo_86": "Heavy snow showers",
        "wmo_95": "Thunderstorm",
        "wmo_96": "Thunderstorm with slight hail",
        "wmo_99": "Thunderstorm with heavy hail",
        "wmo_unknown": "Unknown",
        "daily_header": "📅 <b>Daily SkyPing forecast</b>",
        "private_only_text": "In groups, please use /weather &lt;city&gt;.",
        "forecast_header": "📆 <b>{days}-day forecast</b> — {place}",
        "forecast_usage": (
            "Usage: <code>/forecast Tehran</code> or "
            "<code>/forecast 7 Tehran</code> (1–7 days, default 3)"
        ),
        "day_today": "Today",
        "day_tomorrow": "Tomorrow",
        "weekday_mon": "Mon",
        "weekday_tue": "Tue",
        "weekday_wed": "Wed",
        "weekday_thu": "Thu",
        "weekday_fri": "Fri",
        "weekday_sat": "Sat",
        "weekday_sun": "Sun",
        "alerts_status_on": (
            "🌧 Rain alerts are <b>ON</b> (threshold {threshold}%).\n"
            "SkyPing checks your saved cities during the day."
        ),
        "alerts_status_off": (
            "🌧 Rain alerts are <b>OFF</b>.\n"
            "Use <code>/alerts on</code> or <code>/alerts on 70</code>."
        ),
        "alerts_enabled": "✅ Rain alerts enabled (threshold {threshold}%).",
        "alerts_disabled": "✅ Rain alerts disabled.",
        "alerts_usage": (
            "Usage:\n"
            "• <code>/alerts</code> — status\n"
            "• <code>/alerts on</code> — enable\n"
            "• <code>/alerts on 70</code> — enable with threshold\n"
            "• <code>/alerts off</code> — disable\n"
            "• <code>/alerts 60</code> — set threshold only"
        ),
        "alerts_need_cities": "Add at least one city with /add before enabling alerts.",
        "alerts_threshold_invalid": "Threshold must be a number between 1 and 100.",
        "rain_alert_header": "⚠️ <b>Rain alert</b>",
        "rain_alert_threshold": "Alert threshold: {threshold}%",
        "inline_type_city": "Type a city name to get weather…",
    },
    "fa": {
        "welcome": (
            "👋 به <b>SkyPing</b> خوش آمدید!\n\n"
            "می‌توانم وضعیت آب‌وهوا را نشان دهم، شهرهای مورد علاقه‌تان را ذخیره کنم "
            "و هر روز پیش‌بینی را به این گفتگو بفرستم.\n\n"
            "<b>راهنمای سریع</b>\n"
            "• نام شهر را بفرستید یا از /weather &lt;شهر&gt; استفاده کنید\n"
            "• /add &lt;شهر&gt; برای ذخیره\n"
            "• /list · /remove · /all برای مدیریت شهرها\n"
            "• /subscribe &lt;شهر&gt; برای پیام روزانه\n"
            "• /forecast [1-7] &lt;شهر&gt; پیش‌بینی چندروزه\n"
            "• /alerts on|off — هشدار باران برای شهرهای ذخیره‌شده\n"
            "• در هر چت: @SkyPingBot &lt;شهر&gt; (حالت اینلاین)\n"
            "• /language برای تغییر زبان\n\n"
            "آب‌وهوای شهر پیش‌فرض:"
        ),
        "help_commands": "از منو استفاده کنید یا یک دستور بنویسید.",
        "choose_language": "🌐 زبان خود را انتخاب کنید:",
        "language_set": "✅ زبان به <b>{language}</b> تغییر کرد.",
        "searching": "🔎 در حال جستجوی <b>{query}</b>…",
        "no_results": "😕 شهری با نام <b>{query}</b> پیدا نشد. املای دیگری امتحان کنید.",
        "api_error": "⚠️ سرویس آب‌وهوا موقتاً در دسترس نیست. لطفاً بعداً دوباره تلاش کنید.",
        "timeout": "⏳ درخواست زمان‌بر شد. لطفاً دوباره تلاش کنید.",
        "select_city": "یک شهر را انتخاب کنید:",
        "expired_selection": "⌛ این انتخاب منقضی شده. لطفاً دوباره جستجو کنید.",
        "weather_header": "📍 <b>{place}</b>",
        "units_set": "✅ واحدها به <b>{units}</b> تنظیم شد.",
        "units_invalid": "نحوه استفاده: /units metric|imperial",
        "city_added": "✅ <b>{place}</b> به لیست شما اضافه شد.",
        "city_already": "ℹ️ <b>{place}</b> از قبل در لیست شماست.",
        "city_limit": "⚠️ به سقف {max} شهر رسیده‌اید. ابتدا با /remove یکی را حذف کنید.",
        "city_removed": "🗑 <b>{place}</b> حذف شد.",
        "no_cities": "📭 هنوز شهری ذخیره نکرده‌اید. از /add &lt;شهر&gt; استفاده کنید.",
        "list_title": "🏙 شهرهای ذخیره‌شده — برای آب‌وهوا روی یکی بزنید:",
        "remove_title": "🗑 برای حذف، روی شهر بزنید:",
        "all_title": "🌤 آب‌وهوای همه شهرهای شما:",
        "subscribe_ok": "✅ این گفتگو برای آب‌وهوای روزانهٔ <b>{place}</b> مشترک شد.",
        "subscribe_already": "ℹ️ از قبل برای <b>{place}</b> مشترک هستید.",
        "unsubscribe_title": "🔕 برای لغو اشتراک، روی شهر بزنید:",
        "unsubscribed": "✅ اشتراک <b>{place}</b> لغو شد.",
        "no_subscriptions": "📭 اشتراکی فعال نیست. از /subscribe &lt;شهر&gt; استفاده کنید.",
        "settime_usage": "نحوه استفاده: /settime HH:MM  (۲۴ ساعته، مثلاً 07:30)",
        "settime_ok": "✅ ساعت ارسال روزانه روی <b>{time}</b> ({tz}) تنظیم شد.",
        "settimezone_usage": "نحوه استفاده: /settimezone &lt;منطقه زمانی&gt; مثلاً Asia/Tehran",
        "settimezone_invalid": "❌ منطقه زمانی <b>{tz}</b> نامعتبر است. از نام IANA مثل Europe/London استفاده کنید.",
        "settimezone_ok": "✅ منطقه زمانی به <b>{tz}</b> تنظیم شد.",
        "admin_only": "🔒 فقط مدیران گروه می‌توانند اشتراک‌ها را تغییر دهند.",
        "need_city_arg": "لطفاً نام شهر را وارد کنید. مثال: <code>{example}</code>",
        "condition": "وضعیت",
        "temperature": "دما",
        "feels_like": "حس واقعی",
        "today_range": "امروز",
        "wind": "باد",
        "humidity": "رطوبت",
        "precip": "احتمال بارش",
        "wmo_0": "آسمان صاف",
        "wmo_1": "عمدتاً صاف",
        "wmo_2": "نیمه‌ابری",
        "wmo_3": "ابری",
        "wmo_45": "مه",
        "wmo_48": "مه یخ‌زده",
        "wmo_51": "نم‌نم خفیف",
        "wmo_53": "نم‌نم متوسط",
        "wmo_55": "نم‌نم شدید",
        "wmo_56": "نم‌نم یخ‌زده خفیف",
        "wmo_57": "نم‌نم یخ‌زده شدید",
        "wmo_61": "باران خفیف",
        "wmo_63": "باران متوسط",
        "wmo_65": "باران شدید",
        "wmo_66": "باران یخ‌زده خفیف",
        "wmo_67": "باران یخ‌زده شدید",
        "wmo_71": "برف خفیف",
        "wmo_73": "برف متوسط",
        "wmo_75": "برف شدید",
        "wmo_77": "دانه‌های برف",
        "wmo_80": "رگبار خفیف",
        "wmo_81": "رگبار متوسط",
        "wmo_82": "رگبار شدید",
        "wmo_85": "رگبار برف خفیف",
        "wmo_86": "رگبار برف شدید",
        "wmo_95": "رعدوبرق",
        "wmo_96": "رعدوبرق با تگرگ خفیف",
        "wmo_99": "رعدوبرق با تگرگ شدید",
        "wmo_unknown": "نامشخص",
        "daily_header": "📅 <b>پیش‌بینی روزانه SkyPing</b>",
        "private_only_text": "در گروه‌ها لطفاً از /weather &lt;شهر&gt; استفاده کنید.",
        "forecast_header": "📆 <b>پیش‌بینی {days} روزه</b> — {place}",
        "forecast_usage": (
            "نحوه استفاده: <code>/forecast تهران</code> یا "
            "<code>/forecast 7 تهران</code> (۱ تا ۷ روز، پیش‌فرض ۳)"
        ),
        "day_today": "امروز",
        "day_tomorrow": "فردا",
        "weekday_mon": "دوشنبه",
        "weekday_tue": "سه‌شنبه",
        "weekday_wed": "چهارشنبه",
        "weekday_thu": "پنجشنبه",
        "weekday_fri": "جمعه",
        "weekday_sat": "شنبه",
        "weekday_sun": "یکشنبه",
        "alerts_status_on": (
            "🌧 هشدار باران <b>فعال</b> است (آستانه {threshold}٪).\n"
            "SkyPing شهرهای ذخیره‌شده شما را در طول روز چک می‌کند."
        ),
        "alerts_status_off": (
            "🌧 هشدار باران <b>خاموش</b> است.\n"
            "از <code>/alerts on</code> یا <code>/alerts on 70</code> استفاده کنید."
        ),
        "alerts_enabled": "✅ هشدار باران فعال شد (آستانه {threshold}٪).",
        "alerts_disabled": "✅ هشدار باران خاموش شد.",
        "alerts_usage": (
            "نحوه استفاده:\n"
            "• <code>/alerts</code> — وضعیت\n"
            "• <code>/alerts on</code> — فعال\n"
            "• <code>/alerts on 70</code> — فعال با آستانه\n"
            "• <code>/alerts off</code> — خاموش\n"
            "• <code>/alerts 60</code> — فقط تغییر آستانه"
        ),
        "alerts_need_cities": "قبل از فعال‌سازی حداقل یک شهر با /add ذخیره کنید.",
        "alerts_threshold_invalid": "آستانه باید عددی بین ۱ تا ۱۰۰ باشد.",
        "rain_alert_header": "⚠️ <b>هشدار باران</b>",
        "rain_alert_threshold": "آستانه هشدار: {threshold}٪",
        "inline_type_city": "نام شهر را بنویسید تا آب‌وهوا نمایش داده شود…",
    },
}


def t(lang: str, key: str, **kwargs: Any) -> str:
    """Return a translated string for ``lang``, falling back to English."""
    table = _STRINGS.get(lang) or _STRINGS["en"]
    template = table.get(key) or _STRINGS["en"].get(key) or key
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            return template
    return template
