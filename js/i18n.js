/* ── HUTKO — i18n.js ─────────────────────────────────
   MUST load first. Defines t(), setLang(), getLang()
   synchronously before components.js runs.
   ─────────────────────────────────────────────────── */

const TRANSLATIONS = {
  en: {
    nav_home:'Home', nav_shop:'Shop / Order', nav_about:'About Us',
    nav_delivery:'Delivery & Info', nav_contact:'Contact',
    nav_search:'Search products…', nav_signin:'Sign in',
    nav_myaccount:'My account', nav_myorders:'My orders',
    nav_signout:'Sign out', nav_cart:'Cart', nav_register:'Register',
    footer_tagline:'Authentic Ukrainian frozen food, delivered with love across the Netherlands.',
    footer_pages:'Pages', footer_products:'Products', footer_contact:'Contact',
    footer_copy:'© 2025 HUTKO Frozen Food. All rights reserved.',
    home_hero_tag:'Ukrainian Frozen Food',
    home_hero_title:'Made with love,<br>delivered <em>fast</em>',
    home_hero_sub:'Authentic Ukrainian dishes — frozen fresh, delivered across the Netherlands.',
    home_order_now:'Order now', home_our_story:'Our story',
    home_menu_label:'Our menu', home_menu_title:'Frozen & ready to love',
    home_view_all:'View all products',
    home_delivery_label:'Delivery area',
    home_delivery_title:'We deliver across the Netherlands',
    home_delivery_sub:'Order your favourite Ukrainian frozen dishes and receive them anywhere in the Netherlands.',
    home_delivery_cta:'Check delivery info',
    home_partners_label:'Our partners', home_partners_title:'Trusted by',
    shop_label:'Frozen food', shop_title:'Shop & Order',
    shop_cat_all:'All products', shop_cat_soups:'Soups',
    shop_cat_snacks:'Snacks & Bites', shop_cat_breakfast:'Breakfast',
    shop_cat_mains:'Main dishes', shop_sort:'Sort by',
    shop_sort_featured:'Featured', shop_sort_price_asc:'Price: low to high',
    shop_sort_price_desc:'Price: high to low', shop_sort_name:'Name: A–Z',
    shop_search:'Search products…', shop_add:'Add to cart', shop_added:'Added ✓', shop_from:'from',
    cart_title:'Your order', cart_empty:'Your cart is empty.\nAdd some delicious food!',
    cart_total:'Total', cart_checkout:'Proceed to checkout →',
    checkout_label:'Almost there', checkout_title:'Checkout',
    checkout_contact:'Contact information', checkout_address:'Delivery address',
    checkout_method:'Delivery method', checkout_payment:'Payment',
    checkout_fname:'First name', checkout_lname:'Last name',
    checkout_email:'Email address', checkout_phone:'Phone number',
    checkout_street:'Street address', checkout_postcode:'Postcode',
    checkout_city:'City', checkout_province:'Province',
    checkout_notes:'Delivery notes',
    checkout_notes_ph:'e.g. Ring bell 2nd floor, leave at door…',
    checkout_standard:'Standard delivery',
    checkout_standard_desc:'2–3 business days · Insulated packaging',
    checkout_express:'Express delivery',
    checkout_express_desc:'Next business day · Priority packaging',
    checkout_free:'Free delivery', checkout_free_desc:'Available on orders over €60',
    checkout_payment_title:'Payment on delivery or via invoice',
    checkout_payment_desc:'We accept bank transfer or cash on delivery. After placing your order we\'ll send a confirmation and invoice by email within 1 hour.',
    checkout_summary:'Order summary', checkout_subtotal:'Subtotal',
    checkout_delivery:'Delivery', checkout_place:'Place order →',
    checkout_note:'By placing your order you agree to our delivery terms.',
    checkout_success_title:'Order placed!',
    checkout_success_desc:'Thank you for your order. We\'ll send a confirmation email within 1 hour.',
    checkout_view_orders:'View my orders', checkout_continue:'Continue shopping',
    checkout_empty_title:'Your cart is empty',
    checkout_empty_desc:'Add some products before checking out.',
    checkout_browse:'Browse products',
    login_title:'Welcome back',
    login_sub:'Sign in to track your orders and manage your account.',
    login_email:'Email address', login_pass:'Password', login_btn:'Sign in',
    login_no_account:'Don\'t have an account?', login_register:'Register here',
    login_back:'← Back to homepage',
    login_error:'Incorrect email or password. Please try again.',
    reg_title:'Create account',
    reg_sub:'Join HUTKO to track orders and save your delivery details.',
    reg_fname:'First name', reg_lname:'Last name', reg_email:'Email address',
    reg_phone:'Phone number', reg_pass:'Password', reg_pass2:'Confirm password',
    reg_btn:'Create account', reg_have_account:'Already have an account?', reg_signin:'Sign in',
    account_label:'Your HUTKO account', account_orders:'📦 My orders',
    account_profile:'👤 Profile', account_address:'📍 Saved address',
    account_signout:'↩ Sign out',
    account_no_orders:'You haven\'t placed any orders yet.',
    account_shop:'Start shopping', account_save_profile:'Save changes',
    account_save_address:'Save address', account_change_pass:'Change password',
    account_new_pass:'New password', account_confirm_pass:'Confirm new password',
    account_street:'Street address', account_post:'Postcode',
    account_city:'City', account_province:'Province',
    about_hero_label:'Our story',
    about_hero_title:'Made with love, rooted in tradition',
    about_hero_sub:'A small Ukrainian family business bringing the warmth of home cooking to the Netherlands.',
    about_story_label:'Who we are', about_story_title:'The HUTKO story',
    about_food_label:'A rich culinary heritage', about_food_title:'The soul of Ukrainian cuisine',
    about_dishes_label:'Our menu, our heritage', about_dishes_title:'A story behind every dish',
    about_nl_label:'Stay connected', about_nl_title:'Want to know more?',
    about_nl_sub:'Subscribe to our newsletter for Ukrainian food stories, new dishes, recipes and exclusive offers.',
    about_nl_placeholder:'Your email address', about_nl_btn:'Subscribe',
    about_nl_note:'No spam, ever. Unsubscribe at any time.',
    about_nl_success:'You\'re subscribed! Welcome to the HUTKO community.',
    delivery_label:'Getting your food', delivery_title:'Delivery & Info',
    delivery_sub:'Everything you need to know about how we get HUTKO frozen food from our kitchen to your door.',
    delivery_process_label:'The process', delivery_process_title:'How delivery works',
    delivery_coverage_label:'Coverage', delivery_coverage_title:'Where we deliver',
    delivery_join_label:'Work with us', delivery_join_title:'Join the HUTKO team',
    delivery_driver_title:'Part-time delivery driver', delivery_partner_title:'Become a partner',
    delivery_driver_btn:'Apply as driver', delivery_partner_btn:'Apply as partner',
    contact_label:'Get in touch', contact_title:'We\'d love to hear from you',
    contact_sub:'Whether you have a question about an order, want to collaborate, or just want to say hello — we\'re here.',
    contact_follow:'Follow us on social', contact_form_label:'Send a message',
    contact_form_title:'How can we help?', contact_name:'Full name',
    contact_email:'Email address', contact_phone:'Phone number', contact_social:'Social media',
    contact_topic:'Question regarding', contact_topic_ph:'Select a topic…',
    contact_topic_media:'Media & press', contact_topic_order:'Ordering or cancelling',
    contact_topic_work:'Apply for work', contact_topic_partner:'Become a partner',
    contact_topic_other:'Other', contact_msg_title:'Message title',
    contact_msg_title_ph:'Give your message a short title…',
    contact_msg_body:'Your message', contact_msg_body_ph:'Write your message here…',
    contact_send:'Send message →', contact_success_title:'Message sent!',
    contact_success_desc:'Thank you for reaching out. We\'ll get back to you within 2 business days.',
    search_title:'Search results', search_for:'Results for',
    search_none:'No products found for', search_all:'Browse all products',
  },

  ua: {
    nav_home:'Головна', nav_shop:'Магазин / Замовлення', nav_about:'Про нас',
    nav_delivery:'Доставка та інфо', nav_contact:'Контакти',
    nav_search:'Пошук продуктів…', nav_signin:'Увійти',
    nav_myaccount:'Мій акаунт', nav_myorders:'Мої замовлення',
    nav_signout:'Вийти', nav_cart:'Кошик', nav_register:'Реєстрація',
    footer_tagline:'Справжня українська заморожена їжа, приготована з любов\'ю для Нідерландів.',
    footer_pages:'Сторінки', footer_products:'Продукти', footer_contact:'Контакти',
    footer_copy:'© 2025 HUTKO Frozen Food. Всі права захищені.',
    home_hero_tag:'Українська заморожена їжа',
    home_hero_title:'З любов\'ю,<br>доставка <em>швидко</em>',
    home_hero_sub:'Справжні українські страви — заморожені свіжими, доставляємо по всіх Нідерландах.',
    home_order_now:'Замовити зараз', home_our_story:'Наша історія',
    home_menu_label:'Наше меню', home_menu_title:'Заморожене — з душею',
    home_view_all:'Переглянути всі продукти',
    home_delivery_label:'Зона доставки',
    home_delivery_title:'Доставляємо по всіх Нідерландах',
    home_delivery_sub:'Замовляйте улюблені українські страви — доставимо будь-куди в Нідерландах.',
    home_delivery_cta:'Деталі доставки',
    home_partners_label:'Наші партнери', home_partners_title:'Нам довіряють',
    shop_label:'Заморожена їжа', shop_title:'Магазин та замовлення',
    shop_cat_all:'Всі продукти', shop_cat_soups:'Супи',
    shop_cat_snacks:'Закуски', shop_cat_breakfast:'Сніданок',
    shop_cat_mains:'Основні страви', shop_sort:'Сортування',
    shop_sort_featured:'Рекомендовані', shop_sort_price_asc:'Ціна: від меншої',
    shop_sort_price_desc:'Ціна: від більшої', shop_sort_name:'Назва: А–Я',
    shop_search:'Пошук продуктів…', shop_add:'До кошика', shop_added:'Додано ✓', shop_from:'від',
    cart_title:'Ваше замовлення', cart_empty:'Ваш кошик порожній.\nДодайте смачну їжу!',
    cart_total:'Разом', cart_checkout:'Оформити замовлення →',
    checkout_label:'Майже готово', checkout_title:'Оформлення замовлення',
    checkout_contact:'Контактна інформація', checkout_address:'Адреса доставки',
    checkout_method:'Спосіб доставки', checkout_payment:'Оплата',
    checkout_fname:'Ім\'я', checkout_lname:'Прізвище',
    checkout_email:'Електронна пошта', checkout_phone:'Номер телефону',
    checkout_street:'Вулиця та номер', checkout_postcode:'Поштовий індекс',
    checkout_city:'Місто', checkout_province:'Провінція',
    checkout_notes:'Примітки до доставки',
    checkout_notes_ph:'Напр. дзвоніть на 2-й поверх, залишити біля дверей…',
    checkout_standard:'Стандартна доставка',
    checkout_standard_desc:'2–3 робочих дні · Ізольована упаковка',
    checkout_express:'Експрес-доставка',
    checkout_express_desc:'Наступний робочий день · Пріоритетна упаковка',
    checkout_free:'Безкоштовна доставка', checkout_free_desc:'При замовленні від €60',
    checkout_payment_title:'Оплата при доставці або за рахунком',
    checkout_payment_desc:'Ми приймаємо банківський переказ або готівку при доставці.',
    checkout_summary:'Підсумок замовлення', checkout_subtotal:'Підсума',
    checkout_delivery:'Доставка', checkout_place:'Підтвердити замовлення →',
    checkout_note:'Оформлюючи замовлення, ви погоджуєтесь з нашими умовами доставки.',
    checkout_success_title:'Замовлення оформлено!',
    checkout_success_desc:'Дякуємо за замовлення. Надішлемо підтвердження протягом 1 години.',
    checkout_view_orders:'Мої замовлення', checkout_continue:'Продовжити покупки',
    checkout_empty_title:'Ваш кошик порожній',
    checkout_empty_desc:'Додайте продукти перед оформленням.',
    checkout_browse:'До магазину',
    login_title:'З поверненням',
    login_sub:'Увійдіть, щоб відстежувати замовлення та керувати акаунтом.',
    login_email:'Електронна пошта', login_pass:'Пароль', login_btn:'Увійти',
    login_no_account:'Немає акаунту?', login_register:'Зареєструватися',
    login_back:'← На головну', login_error:'Неправильна пошта або пароль.',
    reg_title:'Створити акаунт',
    reg_sub:'Приєднуйтесь до HUTKO — відстежуйте замовлення та зберігайте адресу.',
    reg_fname:'Ім\'я', reg_lname:'Прізвище', reg_email:'Електронна пошта',
    reg_phone:'Номер телефону', reg_pass:'Пароль', reg_pass2:'Підтвердження паролю',
    reg_btn:'Створити акаунт', reg_have_account:'Вже є акаунт?', reg_signin:'Увійти',
    account_label:'Ваш акаунт HUTKO', account_orders:'📦 Мої замовлення',
    account_profile:'👤 Профіль', account_address:'📍 Збережена адреса',
    account_signout:'↩ Вийти', account_no_orders:'У вас ще немає замовлень.',
    account_shop:'До магазину', account_save_profile:'Зберегти зміни',
    account_save_address:'Зберегти адресу', account_change_pass:'Змінити пароль',
    account_new_pass:'Новий пароль', account_confirm_pass:'Підтвердьте пароль',
    account_street:'Вулиця та номер', account_post:'Поштовий індекс',
    account_city:'Місто', account_province:'Провінція',
    about_hero_label:'Наша історія', about_hero_title:'З любов\'ю — і з традицією',
    about_hero_sub:'Маленький українській сімейний бізнес, що привозить тепло домашньої кухні до Нідерландів.',
    about_story_label:'Хто ми', about_story_title:'Історія HUTKO',
    about_food_label:'Багата кулінарна спадщина', about_food_title:'Душа української кухні',
    about_dishes_label:'Наше меню — наша спадщина', about_dishes_title:'За кожною стравою — своя історія',
    about_nl_label:'Залишайтесь на зв\'язку', about_nl_title:'Хочете дізнатися більше?',
    about_nl_sub:'Підписуйтесь на розсилку — отримуйте рецепти, новини та спеціальні пропозиції.',
    about_nl_placeholder:'Ваша електронна пошта', about_nl_btn:'Підписатися',
    about_nl_note:'Без спаму. Відписатися можна будь-коли.',
    about_nl_success:'Ви підписані! Ласкаво просимо до спільноти HUTKO.',
    delivery_label:'Як отримати замовлення', delivery_title:'Доставка та інфо',
    delivery_sub:'Все, що вам потрібно знати про доставку HUTKO — від нашої кухні до вашого дому.',
    delivery_process_label:'Як це працює', delivery_process_title:'Процес доставки',
    delivery_coverage_label:'Зона покриття', delivery_coverage_title:'Куди доставляємо',
    delivery_join_label:'Робота з нами', delivery_join_title:'Приєднуйтесь до команди HUTKO',
    delivery_driver_title:'Кур\'єр на часткову зайнятість', delivery_partner_title:'Стати партнером',
    delivery_driver_btn:'Подати заявку як кур\'єр', delivery_partner_btn:'Стати партнером',
    contact_label:'Зв\'яжіться з нами', contact_title:'Раді почути від вас',
    contact_sub:'Є питання щодо замовлення, хочете співпрацювати або просто привітатися — ми тут.',
    contact_follow:'Слідкуйте за нами', contact_form_label:'Написати нам',
    contact_form_title:'Чим можемо допомогти?', contact_name:'Повне ім\'я',
    contact_email:'Електронна пошта', contact_phone:'Номер телефону',
    contact_social:'Соціальні мережі', contact_topic:'Тема звернення',
    contact_topic_ph:'Оберіть тему…', contact_topic_media:'Медіа та преса',
    contact_topic_order:'Замовлення або скасування', contact_topic_work:'Робота',
    contact_topic_partner:'Партнерство', contact_topic_other:'Інше',
    contact_msg_title:'Тема повідомлення',
    contact_msg_title_ph:'Коротко опишіть тему…',
    contact_msg_body:'Ваше повідомлення', contact_msg_body_ph:'Напишіть своє повідомлення тут…',
    contact_send:'Надіслати →', contact_success_title:'Повідомлення надіслано!',
    contact_success_desc:'Дякуємо за звернення. Ми відповімо протягом 2 робочих днів.',
    search_title:'Результати пошуку', search_for:'Результати для',
    search_none:'Продуктів не знайдено для', search_all:'Переглянути всі продукти',
  },

  nl: {
    nav_home:'Home', nav_shop:'Winkel / Bestellen', nav_about:'Over ons',
    nav_delivery:'Bezorging & info', nav_contact:'Contact',
    nav_search:'Zoek producten…', nav_signin:'Inloggen',
    nav_myaccount:'Mijn account', nav_myorders:'Mijn bestellingen',
    nav_signout:'Uitloggen', nav_cart:'Winkelwagen', nav_register:'Registreren',
    footer_tagline:'Authentiek Oekraïens diepvriesvoedsel, met liefde bezorgd door heel Nederland.',
    footer_pages:'Pagina\'s', footer_products:'Producten', footer_contact:'Contact',
    footer_copy:'© 2025 HUTKO Frozen Food. Alle rechten voorbehouden.',
    home_hero_tag:'Oekraïens Diepvriesvoedsel',
    home_hero_title:'Met liefde gemaakt,<br><em>snel</em> bezorgd',
    home_hero_sub:'Authentieke Oekraïense gerechten — vers ingevroren, bezorgd door heel Nederland.',
    home_order_now:'Bestel nu', home_our_story:'Ons verhaal',
    home_menu_label:'Ons menu', home_menu_title:'Ingevroren met liefde',
    home_view_all:'Bekijk alle producten',
    home_delivery_label:'Bezorggebied',
    home_delivery_title:'Wij bezorgen door heel Nederland',
    home_delivery_sub:'Bestel uw favoriete Oekraïense gerechten en ontvang ze overal in Nederland.',
    home_delivery_cta:'Bezorginformatie',
    home_partners_label:'Onze partners', home_partners_title:'Vertrouwd door',
    shop_label:'Diepvriesvoedsel', shop_title:'Winkel & Bestellen',
    shop_cat_all:'Alle producten', shop_cat_soups:'Soepen',
    shop_cat_snacks:'Snacks & hapjes', shop_cat_breakfast:'Ontbijt',
    shop_cat_mains:'Hoofdgerechten', shop_sort:'Sorteren op',
    shop_sort_featured:'Aanbevolen', shop_sort_price_asc:'Prijs: laag naar hoog',
    shop_sort_price_desc:'Prijs: hoog naar laag', shop_sort_name:'Naam: A–Z',
    shop_search:'Zoek producten…', shop_add:'In winkelwagen', shop_added:'Toegevoegd ✓', shop_from:'vanaf',
    cart_title:'Uw bestelling', cart_empty:'Uw winkelwagen is leeg.\nVoeg heerlijk eten toe!',
    cart_total:'Totaal', cart_checkout:'Naar afrekenen →',
    checkout_label:'Bijna klaar', checkout_title:'Afrekenen',
    checkout_contact:'Contactgegevens', checkout_address:'Bezorgadres',
    checkout_method:'Bezorgmethode', checkout_payment:'Betaling',
    checkout_fname:'Voornaam', checkout_lname:'Achternaam',
    checkout_email:'E-mailadres', checkout_phone:'Telefoonnummer',
    checkout_street:'Straat en huisnummer', checkout_postcode:'Postcode',
    checkout_city:'Stad', checkout_province:'Provincie',
    checkout_notes:'Bezorginstructies',
    checkout_notes_ph:'Bijv. bel op de 2e verdieping, bij de deur laten…',
    checkout_standard:'Standaard bezorging',
    checkout_standard_desc:'2–3 werkdagen · Geïsoleerde verpakking',
    checkout_express:'Spoedlevering',
    checkout_express_desc:'Volgende werkdag · Prioriteitsverpakking',
    checkout_free:'Gratis bezorging', checkout_free_desc:'Beschikbaar bij bestellingen boven €60',
    checkout_payment_title:'Betaling bij levering of via factuur',
    checkout_payment_desc:'Wij accepteren bankoverschrijving of contant bij levering.',
    checkout_summary:'Bestellingsoverzicht', checkout_subtotal:'Subtotaal',
    checkout_delivery:'Bezorging', checkout_place:'Bestelling plaatsen →',
    checkout_note:'Door uw bestelling te plaatsen gaat u akkoord met onze leveringsvoorwaarden.',
    checkout_success_title:'Bestelling geplaatst!',
    checkout_success_desc:'Bedankt voor uw bestelling. Wij sturen u binnen 1 uur een bevestigingsmail.',
    checkout_view_orders:'Mijn bestellingen', checkout_continue:'Verder winkelen',
    checkout_empty_title:'Uw winkelwagen is leeg',
    checkout_empty_desc:'Voeg producten toe voordat u afrekent.',
    checkout_browse:'Bekijk producten',
    login_title:'Welkom terug',
    login_sub:'Log in om uw bestellingen te volgen en uw account te beheren.',
    login_email:'E-mailadres', login_pass:'Wachtwoord', login_btn:'Inloggen',
    login_no_account:'Nog geen account?', login_register:'Registreer hier',
    login_back:'← Terug naar home', login_error:'Onjuist e-mailadres of wachtwoord.',
    reg_title:'Account aanmaken',
    reg_sub:'Word lid van HUTKO — volg bestellingen en sla uw bezorgadres op.',
    reg_fname:'Voornaam', reg_lname:'Achternaam', reg_email:'E-mailadres',
    reg_phone:'Telefoonnummer', reg_pass:'Wachtwoord', reg_pass2:'Wachtwoord bevestigen',
    reg_btn:'Account aanmaken', reg_have_account:'Al een account?', reg_signin:'Inloggen',
    account_label:'Uw HUTKO-account', account_orders:'📦 Mijn bestellingen',
    account_profile:'👤 Profiel', account_address:'📍 Opgeslagen adres',
    account_signout:'↩ Uitloggen', account_no_orders:'U heeft nog geen bestellingen geplaatst.',
    account_shop:'Begin met winkelen', account_save_profile:'Wijzigingen opslaan',
    account_save_address:'Adres opslaan', account_change_pass:'Wachtwoord wijzigen',
    account_new_pass:'Nieuw wachtwoord', account_confirm_pass:'Wachtwoord bevestigen',
    account_street:'Straat en huisnummer', account_post:'Postcode',
    account_city:'Stad', account_province:'Provincie',
    about_hero_label:'Ons verhaal', about_hero_title:'Met liefde gemaakt, geworteld in traditie',
    about_hero_sub:'Een klein Oekraïens familiebedrijf dat de warmte van de thuiskeuken naar Nederland brengt.',
    about_story_label:'Wie wij zijn', about_story_title:'Het HUTKO-verhaal',
    about_food_label:'Een rijke culinaire erfenis', about_food_title:'De ziel van de Oekraïense keuken',
    about_dishes_label:'Ons menu, ons erfgoed', about_dishes_title:'Achter elk gerecht schuilt een verhaal',
    about_nl_label:'Blijf verbonden', about_nl_title:'Meer weten?',
    about_nl_sub:'Abonneer u op onze nieuwsbrief voor Oekraïense kookverhalen, nieuwe gerechten en exclusieve aanbiedingen.',
    about_nl_placeholder:'Uw e-mailadres', about_nl_btn:'Abonneren',
    about_nl_note:'Geen spam. Uitschrijven kan altijd.',
    about_nl_success:'U bent geabonneerd! Welkom bij de HUTKO-gemeenschap.',
    delivery_label:'Uw bestelling ontvangen', delivery_title:'Bezorging & info',
    delivery_sub:'Alles wat u moet weten over hoe wij HUTKO-diepvriesvoedsel bij u bezorgen.',
    delivery_process_label:'Het proces', delivery_process_title:'Hoe bezorging werkt',
    delivery_coverage_label:'Dekking', delivery_coverage_title:'Waar wij bezorgen',
    delivery_join_label:'Werk met ons', delivery_join_title:'Word deel van het HUTKO-team',
    delivery_driver_title:'Bezorger parttime', delivery_partner_title:'Word partner',
    delivery_driver_btn:'Solliciteer als bezorger', delivery_partner_btn:'Word partner',
    contact_label:'Neem contact op', contact_title:'Wij horen graag van u',
    contact_sub:'Heeft u een vraag over een bestelling, wilt u samenwerken of gewoon hallo zeggen — wij zijn er.',
    contact_follow:'Volg ons', contact_form_label:'Stuur een bericht',
    contact_form_title:'Hoe kunnen wij helpen?', contact_name:'Volledige naam',
    contact_email:'E-mailadres', contact_phone:'Telefoonnummer', contact_social:'Social media',
    contact_topic:'Vraag betreft', contact_topic_ph:'Kies een onderwerp…',
    contact_topic_media:'Media & pers', contact_topic_order:'Bestellen of annuleren',
    contact_topic_work:'Sollicitatie', contact_topic_partner:'Partner worden',
    contact_topic_other:'Overig', contact_msg_title:'Onderwerp',
    contact_msg_title_ph:'Geef uw bericht een korte titel…',
    contact_msg_body:'Uw bericht', contact_msg_body_ph:'Schrijf uw bericht hier…',
    contact_send:'Versturen →', contact_success_title:'Bericht verzonden!',
    contact_success_desc:'Bedankt voor uw bericht. Wij reageren binnen 2 werkdagen.',
    search_title:'Zoekresultaten', search_for:'Resultaten voor',
    search_none:'Geen producten gevonden voor', search_all:'Bekijk alle producten',
  }
};

/* ── SYNCHRONOUS ENGINE (runs immediately, before DOMContentLoaded) ── */
const I18N_KEY = 'hutko_lang';

function getLang() {
  return localStorage.getItem(I18N_KEY) || 'en';
}

/* t() — get translation, falls back to EN, then key */
function t(key) {
  const lang = getLang();
  return (TRANSLATIONS[lang] && TRANSLATIONS[lang][key])
    || (TRANSLATIONS['en'] && TRANSLATIONS['en'][key])
    || key;
}

function applyTranslations() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const val = t(el.dataset.i18n);
    if (!val || val === el.dataset.i18n) return;
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
      el.placeholder = val;
    } else {
      el.innerHTML = val;
    }
  });
}

function updateLangSwitcher() {
  const lang = getLang();
  document.querySelectorAll('.lang-switcher button[data-lang]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });
}

function setLang(lang) {
  localStorage.setItem(I18N_KEY, lang);
  /* Re-render navbar and footer with new language */
  if (typeof renderNavbar === 'function') {
    document.getElementById('navbar-placeholder').innerHTML = '';
    renderNavbar();
  }
  if (typeof renderFooter === 'function') {
    document.getElementById('footer-placeholder').innerHTML = '';
    renderFooter();
  }
  if (typeof renderCartPanel === 'function') {
    document.getElementById('cart-placeholder').innerHTML = '';
    renderCartPanel();
    /* Re-attach cart events */
    document.getElementById('cartOverlay')?.addEventListener('click', () => {
      if (typeof toggleCart === 'function') toggleCart();
    });
    document.getElementById('cartClose')?.addEventListener('click', () => {
      if (typeof toggleCart === 'function') toggleCart();
    });
    if (typeof updateCartUI === 'function') updateCartUI();
  }
  /* Apply to all static data-i18n elements on the page */
  applyTranslations();
  updateLangSwitcher();
  /* Re-init search on new navbar */
  if (typeof initSearch === 'function') setTimeout(initSearch, 50);
}

/* Expose globally — synchronously, before any other script */
window.t = t;
window.getLang = getLang;
window.setLang = setLang;
window.applyTranslations = applyTranslations;

/* Apply on DOM ready */
document.addEventListener('DOMContentLoaded', () => {
  updateLangSwitcher();
  applyTranslations();
});
