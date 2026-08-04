"""Member churches offered as suggestions on the registration form.

Presented through a ``<datalist>``, so a camper can pick from the list or type
any church that isn't on it. The previous form used a ``<select>`` plus a
hidden ``<input>`` that shared the same ``id`` and ``name``, toggled by jQuery.

Editing this list is the only step needed to add a church.
"""

CHURCH_CHOICES = [
    "СЛАВЯНСКАЯ БАПТИСТСКАЯ ЦЕРКОВЬ 'БЛАГОДАТЬ' (VANCOUVER, WA)",
    "ЦЕРКОВЬ 'ВОЗРОЖДЕНИЕ' (VANCOUVER, WA)",
    "ПЕРВАЯ СЛАВЯНСКАЯ ЦЕРКОВЬ 'ВЕФИЛЬ' (EAST WENATCHEE, WA)",
    "СЛАВЯНСКАЯ БАПТИСТСКАЯ ЦЕРКОВЬ 'ИСТОЧНИК ЖИЗНИ' (MUKILTEO, WA)",
    "ПЕРВАЯ СЛАВЯНСКАЯ ЦЕРКОВЬ ЕХБ 'CHURCH OF LOVE' (OREGON CITY, OR)",
    "ЦЕРКОВЬ 'СВЕТ СПАСЕНИЯ' (CARMICHAEL, CA)",
    "СЛАВЯНСКАЯ БАПТИСТСКАЯ ЦЕРКОВЬ (BELLINGHAM, WA)",
    "СЛАВЯНСКАЯ ЦЕРКОВЬ 'СВЕТ ЕВАНГЕЛИЯ' (SPOKANE, WA)",
    "ЦЕРКОВЬ 'НОВАЯ ЖИЗНЬ' (SALEM, OR)",
    "ЦЕРКОВЬ 'ГОЛГОФА' (VANCOUVER, WA)",
    "ЦЕРКОВЬ 'БЛАГОВЕСТИЕ' (DES MOINES, WA)",
    "ЦЕРКОВЬ 'ВОЗРОЖДЕНИЕ' (FEDERAL WAY, WA)",
    "ЦЕРКОВЬ 'ВИФАНИЯ' (FEDERAL WAY, WA)",
    "ЦЕРКОВЬ 'НАДЕЖДА' (EVERETT, WA)",
    "ЦЕРКОВЬ ЕХБ (KIRKLAND, WA)",
    "СЛАВЯНСКАЯ БАПТИСТСКАЯ ЦЕРКОВЬ Г. СИЭТЛА (LYNNWOOD, WA)",
    "ОБЪЕДИНЕННАЯ ЦЕРКОВЬ ЕХБ (TACOMA, WA)",
    "ПЕРВАЯ СЛАВЯНСКАЯ БАПТИСТСКАЯ ЦЕРКОВЬ (SALEM, OR)",
    "ЦЕРКОВЬ 'БЛАГОДАТЬ' (LAKEWOOD, WA)",
    "ЦЕРКОВЬ 'СЛОВО ЖИЗНИ' (PORTLAND, OR)",
    "ЦЕРКОВЬ 'ЭММАНУИЛ' (VANCOUVER, WA)",
    "ЦЕРКОВЬ 'СПАСЕНИЕ' (EDGEWOOD, WA)",
    "ЦЕРКОВЬ 'БЛАГОДАТЬ' (MERIDIAN, ID)",
    "ЦЕРКОВЬ 'ПИЛИГРИМ' (SPOKANE, WA)",
    "ЦЕРКОВЬ 'НА ГОРЕ' (SPOKANE, WA)",
    "СЛАВЯНСКАЯ ЕВАНГЕЛЬСКАЯ БАПТИСТСКАЯ ЦЕРКОВЬ (VANCOUVER, BC)",
    "ЦЕРКОВЬ 'НАДЕЖДА' (KELOWNA, BC)",
]
