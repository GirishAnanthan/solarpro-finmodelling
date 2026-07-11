"""
SolarPro Financial Modelling — Multi-Language i18n Engine
Supports: English, Hindi, Gujarati, Chinese, Arabic (RTL), German, Spanish, Greek, Latin
"""
from config import RTL_LANGUAGES

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── Navigation ──────────────────────────────────────────────────────────
    "nav_customer_project": {"en":"👤 Customer & Project","hi":"👤 ग्राहक और परियोजना","gu":"👤 ગ્રાહક અને પ્રોજેક્ટ","zh":"👤 客户与项目","ar":"👤 العميل والمشروع","de":"👤 Kunde & Projekt","es":"👤 Cliente y Proyecto","el":"👤 Πελάτης & Έργο","la":"👤 Cliens et Projectum"},
    "nav_financial_inputs":{"en":"💳 Financial Inputs","hi":"💳 वित्तीय इनपुट","gu":"💳 નાણાકીય ઇનપુટ્સ","zh":"💳 财务输入","ar":"💳 المدخلات المالية","de":"💳 Finanzielle Eingaben","es":"💳 Entradas Financieras","el":"💳 Χρηματοοικονομικές Είσοδοι","la":"💳 Initia Pecuniaria"},
    "nav_module_compare":  {"en":"📋 Module Compare","hi":"📋 मॉड्यूल तुलना","gu":"📋 મોડ્યુલ સરખામણી","zh":"📋 组件对比","ar":"📋 مقارنة الألواح","de":"📋 Modulvergleich","es":"📋 Comparar Módulos","el":"📋 Σύγκριση Πάνελ","la":"📋 Comparatio Modulorum"},
    "nav_generate_report": {"en":"📊 Generate Report","hi":"📊 रिपोर्ट बनाएं","gu":"📊 રિપોર્ટ બનાવો","zh":"📊 生成报告","ar":"📊 إنشاء تقرير","de":"📊 Bericht erstellen","es":"📊 Generar Informe","el":"📊 Δημιουργία Αναφοράς","la":"📊 Relatio Creare"},
    "nav_performance":     {"en":"📊 Performance","hi":"📊 प्रदर्शन","gu":"📊 કામગીરી","zh":"📊 性能分析","ar":"📊 الأداء","de":"📊 Leistung","es":"📊 Rendimiento","el":"📊 Απόδοση","la":"📊 Effectus"},
    "nav_compliance":      {"en":"✅ Compliance","hi":"✅ अनुपालन","gu":"✅ અનુપાલન","zh":"✅ 合规检查","ar":"✅ الامتثال","de":"✅ Compliance","es":"✅ Cumplimiento","el":"✅ Συμμόρφωση","la":"✅ Conformitas"},
    "nav_reports":         {"en":"📄 Reports & Billing","hi":"📄 रिपोर्ट और बिलिंग","gu":"📄 અહેવાલ અને બિલિંગ","zh":"📄 报告与账单","ar":"📄 التقارير والفواتير","de":"📄 Berichte & Abrechnung","es":"📄 Informes y Facturación","el":"📄 Αναφορές & Χρέωση","la":"📄 Relationes et Ratio"},
    # ── App Shell ───────────────────────────────────────────────────────────
    "app_tagline":      {"en":"Ground-Mounted Solar Financial Intelligence","hi":"ग्राउंड-माउंटेड सोलर वित्तीय विश्लेषण","gu":"ગ્રાઉન્ડ-માઉન્ટેડ સોલર ફાઇનાન્શિયલ ઇન્ટેલિજન્સ","zh":"地面光伏财务智能平台","ar":"ذكاء مالي للطاقة الشمسية الأرضية","de":"Boden-Solaranlage Finanzintelligenz","es":"Inteligencia Financiera Solar en Suelo","el":"Χρηματοοικονομική Ανάλυση Ηλιακής Ενέργειας","la":"Intelligentia Pecuniaria Solis Terrestris"},
    "language_label":   {"en":"Language","hi":"भाषा","gu":"ભાષા","zh":"语言","ar":"اللغة","de":"Sprache","es":"Idioma","el":"Γλώσσα","la":"Lingua"},
    "currency_label":   {"en":"Currency","hi":"मुद्रा","gu":"ચલણ","zh":"货币","ar":"العملة","de":"Währung","es":"Moneda","el":"Νόμισμα","la":"Moneta"},
    # ── Ingestion ───────────────────────────────────────────────────────────
    "upload_json":      {"en":"Upload AutoLISP JSON","hi":"AutoLISP JSON अपलोड करें","gu":"AutoLISP JSON અપલોડ કરો","zh":"上传 AutoLISP JSON","ar":"رفع ملف AutoLISP JSON","de":"AutoLISP JSON hochladen","es":"Subir AutoLISP JSON","el":"Ανέβασμα AutoLISP JSON","la":"Elige JSON AutoLISP"},
    "project_name":     {"en":"Project Name","hi":"परियोजना का नाम","gu":"પ્રોજેક્ટ નામ","zh":"项目名称","ar":"اسم المشروع","de":"Projektname","es":"Nombre del Proyecto","el":"Όνομα Έργου","la":"Nomen Projecti"},
    "dc_capacity":      {"en":"DC Capacity (kWp)","hi":"DC क्षमता (kWp)","gu":"DC ક્ષમતા (kWp)","zh":"直流容量 (kWp)","ar":"السعة الكهربائية (kWp)","de":"DC-Leistung (kWp)","es":"Capacidad CC (kWp)","el":"Ισχύς DC (kWp)","la":"Capacitas DC (kWp)"},
    "module_count":     {"en":"Module Count","hi":"मॉड्यूल संख्या","gu":"મોડ્યુલ સંખ્યા","zh":"组件数量","ar":"عدد الألواح","de":"Modulanzahl","es":"Cantidad de Módulos","el":"Αριθμός Πάνελ","la":"Numerus Modulorum"},
    "tilt_angle":       {"en":"Tilt Angle (°)","hi":"झुकाव कोण (°)","gu":"ઢળાણ કોણ (°)","zh":"倾斜角 (°)","ar":"زاوية الميل (°)","de":"Neigungswinkel (°)","es":"Ángulo de Inclinación (°)","el":"Γωνία Κλίσης (°)","la":"Angulus Inclinationis (°)"},
    # ── Financial ───────────────────────────────────────────────────────────
    "equity_irr":       {"en":"Equity IRR","hi":"इक्विटी IRR","gu":"ઇક્વિટી IRR","zh":"股权内部收益率","ar":"معدل العائد الداخلي","de":"Eigenkapital-IRR","es":"TIR del Capital","el":"ΕΕΑ Ιδίων Κεφαλαίων","la":"IRR Aequitatis"},
    "project_irr":      {"en":"Project IRR","hi":"परियोजना IRR","gu":"પ્રોજેક્ટ IRR","zh":"项目内部收益率","ar":"معدل عائد المشروع","de":"Projekt-IRR","es":"TIR del Proyecto","el":"ΕΕΑ Έργου","la":"IRR Projecti"},
    "lcoe":             {"en":"LCOE (₹/kWh)","hi":"LCOE (₹/kWh)","gu":"LCOE (₹/kWh)","zh":"平准化电力成本","ar":"تكلفة الطاقة المعيارية","de":"Stromgestehungskosten","es":"LCOE (₹/kWh)","el":"LCOE (₹/kWh)","la":"LCOE (₹/kWh)"},
    "npv":              {"en":"NPV","hi":"शुद्ध वर्तमान मूल्य","gu":"NPV","zh":"净现值","ar":"صافي القيمة الحالية","de":"Kapitalwert","es":"VPN","el":"ΚΠΑ","la":"Valor Praesens"},
    "payback":          {"en":"Payback Period","hi":"वापसी अवधि","gu":"પેબેક પીરિયડ","zh":"回收期","ar":"فترة الاسترداد","de":"Amortisationszeit","es":"Periodo de Recuperación","el":"Περίοδος Αποπληρωμής","la":"Tempus Restitutionis"},
    "sensitivity":      {"en":"P50/P75/P90 Sensitivity","hi":"P50/P75/P90 संवेदनशीलता","gu":"P50/P75/P90 સંવેદનશીલતા","zh":"P50/P75/P90 敏感性分析","ar":"تحليل الحساسية","de":"P50/P75/P90-Sensitivität","es":"Sensibilidad P50/P75/P90","el":"Ανάλυση Ευαισθησίας","la":"Analysis Sensitivitatis"},
    "cash_flows":       {"en":"25-Year Cash Flows","hi":"25-वर्षीय नकदी प्रवाह","gu":"25-વર્ષ રોકડ પ્રવાહ","zh":"25年现金流","ar":"التدفقات النقدية على 25 سنة","de":"25-Jahres-Cashflows","es":"Flujos de Caja 25 Años","el":"Ταμειακές Ροές 25 Ετών","la":"Fluxus Pecuniae XXV Annorum"},
    # ── Performance ─────────────────────────────────────────────────────────
    "upload_excel":     {"en":"Upload Monthly Generation (XLSX)","hi":"मासिक उत्पादन अपलोड करें (XLSX)","gu":"માસિક ઉત્પાદન અપલોડ કરો (XLSX)","zh":"上传月度发电数据 (XLSX)","ar":"رفع بيانات الإنتاج الشهري","de":"Monatliche Erzeugung hochladen (XLSX)","es":"Subir Generación Mensual (XLSX)","el":"Μηνιαία Παραγωγή (XLSX)","la":"Generatio Menstrua (XLSX)"},
    "projected":        {"en":"Projected (kWh)","hi":"अनुमानित (kWh)","gu":"અનુમાનિત (kWh)","zh":"预测 (kWh)","ar":"المتوقع (kWh)","de":"Geplant (kWh)","es":"Proyectado (kWh)","el":"Προβλεπόμενο (kWh)","la":"Praevisa (kWh)"},
    "actual":           {"en":"Actual (kWh)","hi":"वास्तविक (kWh)","gu":"વાસ્તવિક (kWh)","zh":"实际 (kWh)","ar":"الفعلي (kWh)","de":"Tatsächlich (kWh)","es":"Real (kWh)","el":"Πραγματικό (kWh)","la":"Actuale (kWh)"},
    "variance":         {"en":"Variance (%)","hi":"विचरण (%)","gu":"ભિન્નતા (%)","zh":"偏差 (%)","ar":"الانحراف (%)","de":"Abweichung (%)","es":"Varianza (%)","el":"Διακύμανση (%)","la":"Variatio (%)"},
    # ── Compliance ──────────────────────────────────────────────────────────
    "status_pending":   {"en":"Pending","hi":"लंबित","gu":"બાકી","zh":"待处理","ar":"قيد الانتظار","de":"Ausstehend","es":"Pendiente","el":"Εκκρεμεί","la":"Pendet"},
    "status_progress":  {"en":"In Progress","hi":"प्रगति में","gu":"પ્રગતિ માં","zh":"进行中","ar":"قيد التنفيذ","de":"In Bearbeitung","es":"En Proceso","el":"Σε Εξέλιξη","la":"In Progressu"},
    "status_completed": {"en":"Completed","hi":"पूर्ण","gu":"પૂર્ણ","zh":"已完成","ar":"مكتمل","de":"Abgeschlossen","es":"Completado","el":"Ολοκληρώθηκε","la":"Completum"},
    # ── Reports ─────────────────────────────────────────────────────────────
    "download_pdf":     {"en":"Download PDF Report","hi":"PDF रिपोर्ट डाउनलोड करें","gu":"PDF રિપોર્ટ ડાઉનલોડ કરો","zh":"下载PDF报告","ar":"تحميل تقرير PDF","de":"PDF-Bericht herunterladen","es":"Descargar Informe PDF","el":"Λήψη Αναφοράς PDF","la":"Relatio PDF Transferre"},
    "subscribe":        {"en":"Subscribe Now","hi":"अभी सदस्यता लें","gu":"હવે સબ્સ્ક્રાઇબ કરો","zh":"立即订阅","ar":"اشترك الآن","de":"Jetzt abonnieren","es":"Suscribirse Ahora","el":"Εγγραφή Τώρα","la":"Nunc Subscribere"},
    # ── Generic ─────────────────────────────────────────────────────────────
    "calculate":        {"en":"Calculate","hi":"गणना करें","gu":"ગણતરી કરો","zh":"计算","ar":"احسب","de":"Berechnen","es":"Calcular","el":"Υπολογισμός","la":"Computare"},
    "results":          {"en":"Results","hi":"परिणाम","gu":"પરિણામ","zh":"结果","ar":"النتائج","de":"Ergebnisse","es":"Resultados","el":"Αποτελέσματα","la":"Eventus"},
    "year":             {"en":"Year","hi":"वर्ष","gu":"વર્ષ","zh":"年","ar":"سنة","de":"Jahr","es":"Año","el":"Έτος","la":"Annus"},
    "revenue":          {"en":"Revenue","hi":"राजस्व","gu":"આવક","zh":"收入","ar":"الإيرادات","de":"Umsatz","es":"Ingresos","el":"Έσοδα","la":"Reditus"},
    "opex":             {"en":"OPEX","hi":"परिचालन व्यय","gu":"OPEX","zh":"运营成本","ar":"تكاليف التشغيل","de":"Betriebskosten","es":"OPEX","el":"Λειτουργικά Έξοδα","la":"Sumptus Operandi"},
    "dscr":             {"en":"DSCR","hi":"ऋण सेवा कवरेज अनुपात","gu":"DSCR","zh":"偿债覆盖率","ar":"نسبة تغطية خدمة الدين","de":"Schuldendienstdeckungsgrad","es":"DSCR","el":"ΔΚΔΟ","la":"DSCR"},
    "assumptions":      {"en":"Assumptions","hi":"मान्यताएँ","gu":"ધારણાઓ","zh":"假设条件","ar":"الافتراضات","de":"Annahmen","es":"Supuestos","el":"Παραδοχές","la":"Praesumptiones"},
    "generation":       {"en":"Generation (kWh)","hi":"उत्पादन (kWh)","gu":"ઉત્પાદન (kWh)","zh":"发电量 (kWh)","ar":"الإنتاج (kWh)","de":"Erzeugung (kWh)","es":"Generación (kWh)","el":"Παραγωγή (kWh)","la":"Generatio (kWh)"},
    "degradation":      {"en":"Degradation (%)","hi":"अवक्रमण (%)","gu":"અધઃપતન (%)","zh":"衰减率 (%)","ar":"التدهور (%)","de":"Degradation (%)","es":"Degradación (%)","el":"Υποβάθμιση (%)","la":"Degradatio (%)"},
    # ── Datasheet ──────────────────────────────────────────────────────────
    "upload_datasheet": {"en":"Upload Module Datasheets (CSV/XLSX/PDF)","hi":"मॉड्यूल डेटाशीट अपलोड करें","gu":"મોડ્યુલ ડેટાશીટ અપલોડ કરો","zh":"上传组件规格书","ar":"رفع صحائف بيانات الألواح","de":"Moduldatenblätter hochladen","es":"Subir Fichas de Módulos","el":"Ανέβασμα Φύλλων Δεδομένων","la":"Elige Tabulas Modulorum"},
    "compare_btn":      {"en":"Compare Modules","hi":"मॉड्यूल तुलना करें","gu":"મોડ્યુલ સરખામણી કરો","zh":"对比组件","ar":"مقارنة الألواح","de":"Module vergleichen","es":"Comparar Módulos","el":"Σύγκριση Πάνελ","la":"Confer Modulos"},
    "ranking":          {"en":"Module Ranking","hi":"मॉड्यूल रैंकिंग","gu":"મોડ્યુલ રેન્કિંગ","zh":"组件排名","ar":"ترتيب الألواح","de":"Modul-Ranking","es":"Ranking de Módulos","el":"Κατάταξη Πάνελ","la":"Ordo Modulorum"},
    "radar_chart":      {"en":"Radar Comparison","hi":"रडार तुलना","gu":"રડાર સરખામણી","zh":"雷达对比图","ar":"مقارنة الرادار","de":"Radar-Vergleich","es":"Comparación Radar","el":"Σύγκριση Ραντάρ","la":"Comparatio Radar"},
    # ── Weightage ────────────────────────────────────────────────────────────
    "weightage_title":  {"en":"Parameter Weightage for Module Scoring","hi":"मॉड्यूल स्कोरिंग के लिए पैरामीटर वेटेज","gu":"મોડ્યુલ સ્કોરિંગ માટે પેરામિટર વેટેજ","zh":"模块评分参数权重","ar":"أوزان المعايير لتقييم الألواح","de":"Gewichtung der Parameter für Modul-Bewertung","es":"Ponderación de Parámetros para Puntuación de Módulos","el":"Βάρος Παραμέτρων για Βαθμολογία Πάνελ","la":"Ponderatio Parametrorum pro Scoring Modulorum"},
    "max_power":        {"en":"Max Power (Wp)","hi":"अधिकतम पावर (Wp)","gu":"મહત્તમ પાવર (Wp)","zh":"最大功率 (Wp)","ar":"الطاقة القصوى (Wp)","de":"Max. Leistung (Wp)","es":"Potencia Máx. (Wp)","el":"Μέγ. Ισχύς (Wp)","la":"Maxima Potestas (Wp)"},
    "efficiency":       {"en":"Efficiency (%)","hi":"दक्षता (%)","gu":"ક્ષમતા (%)","zh":"效率 (%)","ar":"الكفاءة (%)","de":"Wirkungsgrad (%)","es":"Eficiencia (%)","el":"Απόδοση (%)","la":"Efficientia (%)"},
    "temp_coeff":       {"en":"Temp Coefficient","hi":"तापमान गुणांक","gu":"તાપમાન ગુણાકર","zh":"温度系数","ar":"معامل الحرارة","de":"Temperaturkoeffizient","es":"Coef. Temperatura","el":"Συντελεστής Θερμ.","la":"Coefficients Temperaturs"},
    "warranty":         {"en":"Warranty (yrs)","hi":"वारंटी (वर्ष)","gu":"વોરંટી (વર્ષ)","zh":"质保 (年)","ar":"الضمان (سنوات)","de":"Garantie (Jahre)","es":"Garantía (años)","el":"Εγγύηση (έτη)","la":"Garantia (Anni)"},
    "vmp":              {"en":"Vmp (V)","hi":"Vmp (V)","gu":"Vmp (V)","zh":"Vmp (V)","ar":"Vmp (V)","de":"Vmp (V)","es":"Vmp (V)","el":"Vmp (V)","la":"Vmp (V)"},
    "degradation":      {"en":"Degradation (%/yr)","hi":"अवक्रमण (%/वर्ष)","gu":"અધઃપતન (%/વર્ષ)","zh":"衰减率 (%/年)","ar":"التدهور (%/سنه)","de":"Degradation (%/Jahr)","es":"Degradación (%/año)","el":"Απόβληση (%/έτος)","la":"Degradatio (%/Annum)"},
}


def t(key: str, lang: str = "en") -> str:
    """Return translated string for the given key and language."""
    entry = TRANSLATIONS.get(key, {})
    return entry.get(lang, entry.get("en", key))


def is_rtl(lang: str) -> bool:
    """Return True if the language is right-to-left."""
    return lang in RTL_LANGUAGES


def rtl_css(lang: str) -> str:
    """Return inline CSS string for RTL layout if applicable."""
    if is_rtl(lang):
        return "direction:rtl;text-align:right;"
    return ""


def get_rtl_class(lang: str) -> str:
    return "rtl-layout" if is_rtl(lang) else ""
