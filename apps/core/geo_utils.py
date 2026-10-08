"""
Geo utilities for resolving Indonesian city & TLC coordinates for the dashboard interactive map.
"""
import re

# Comprehensive coordinates mapping for Indonesian Cities, Regencies, and TLCs
CITY_COORDINATES = {
    # DKI Jakarta & Greater Jakarta (Jabodetabek)
    'jakarta': [-6.2088, 106.8456],
    'jakarta pusat': [-6.1805, 106.8284],
    'jakarta selatan': [-6.2615, 106.8106],
    'jakarta barat': [-6.1683, 106.7589],
    'jakarta timur': [-6.2250, 106.9004],
    'jakarta utara': [-6.1384, 106.8640],
    'kepulauan seribu': [-5.6122, 106.5622],
    'bekasi': [-6.2383, 106.9756],
    'bogor': [-6.5971, 106.8060],
    'depok': [-6.4025, 106.7942],
    'tangerang': [-6.1783, 106.6319],
    'tangerang selatan': [-6.2887, 106.7179],
    'tangsel': [-6.2887, 106.7179],

    # Jawa Barat & Banten
    'bandung': [-6.9175, 107.6191],
    'bandung barat': [-6.8447, 107.5028],
    'cimahi': [-6.8722, 107.5422],
    'cirebon': [-6.7320, 108.5523],
    'sukabumi': [-6.9277, 106.9300],
    'tasikmalaya': [-7.3274, 108.2207],
    'banjar': [-7.3699, 108.5337],
    'karawang': [-6.3073, 107.2931],
    'purwakarta': [-6.5569, 107.4433],
    'subang': [-6.5716, 107.7587],
    'indramayu': [-6.3264, 108.3200],
    'sumedang': [-6.8586, 107.9269],
    'garut': [-7.2278, 107.9086],
    'ciamis': [-7.3256, 108.3533],
    'kuningan': [-6.9762, 108.4839],
    'majalengka': [-6.8361, 108.2278],
    'cianjur': [-6.8222, 107.1394],
    'pangandaran': [-7.7022, 108.4947],
    'serang': [-6.1104, 106.1640],
    'cilegon': [-6.0024, 106.0125],
    'pandeglang': [-6.3089, 106.1065],
    'lebak': [-6.3539, 106.2489],

    # Jawa Tengah & DIY
    'semarang': [-6.9667, 110.4167],
    'surakarta': [-7.5755, 110.8243],
    'solo': [-7.5755, 110.8243],
    'magelang': [-7.4706, 110.2178],
    'salatiga': [-7.3305, 110.5084],
    'pekalongan': [-6.8886, 109.6753],
    'tegal': [-6.8694, 109.1402],
    'kudus': [-6.8048, 110.8405],
    'jepara': [-6.5924, 110.6778],
    'pati': [-6.7562, 111.0378],
    'rembang': [-6.7061, 111.3414],
    'blora': [-6.9697, 111.4186],
    'grobogan': [-7.0869, 110.9169],
    'purwodadi': [-7.0869, 110.9169],
    'demak': [-6.8944, 110.6389],
    'kendal': [-6.9242, 110.2039],
    'batang': [-6.9086, 109.7314],
    'pemalang': [-6.8922, 109.3808],
    'brebes': [-6.8703, 109.0417],
    'banyumas': [-7.4244, 109.2303],
    'purwokerto': [-7.4244, 109.2303],
    'cilacap': [-7.7279, 109.0059],
    'purbalingga': [-7.3886, 109.3639],
    'banjarnegara': [-7.3986, 109.6978],
    'kebumen': [-7.6686, 109.6519],
    'purworejo': [-7.7136, 110.0078],
    'wonosobo': [-7.3636, 109.9000],
    'boyolali': [-7.5361, 110.5944],
    'klaten': [-7.7058, 110.6067],
    'sukoharjo': [-7.6833, 110.8333],
    'wonogiri': [-7.8142, 110.9256],
    'karanganyar': [-7.5969, 110.9514],
    'sragen': [-7.4286, 111.0219],
    'temanggung': [-7.3167, 110.1667],
    'yogyakarta': [-7.7956, 110.3695],
    'jogja': [-7.7956, 110.3695],
    'sleman': [-7.7156, 110.3556],
    'bantul': [-7.8897, 110.3289],
    'kulon progo': [-7.8578, 110.1589],
    'wates': [-7.8578, 110.1589],
    'gunungkidul': [-7.9658, 110.6033],
    'wonosari': [-7.9658, 110.6033],

    # Jawa Timur
    'surabaya': [-7.2504, 112.7688],
    'malang': [-7.9666, 112.6326],
    'batu': [-7.8712, 112.5270],
    'kediri': [-7.8480, 112.0178],
    'blitar': [-8.0983, 112.1681],
    'madiun': [-7.6298, 111.5239],
    'mojokerto': [-7.4726, 112.4381],
    'pasuruan': [-7.6453, 112.9075],
    'probolinggo': [-7.7543, 113.2159],
    'sidoarjo': [-7.4478, 112.7183],
    'gresik': [-7.1566, 112.6555],
    'lamongan': [-7.1197, 112.4158],
    'tuban': [-6.8976, 112.0649],
    'bojonegoro': [-7.1500, 111.8819],
    'ngawi': [-7.4042, 111.4464],
    'magetan': [-7.6492, 111.3283],
    'ponorogo': [-7.8686, 111.4622],
    'pacitan': [-8.1969, 111.1067],
    'trenggalek': [-8.0500, 111.7167],
    'tulungagung': [-8.0667, 111.9000],
    'nganjuk': [-7.6050, 111.9039],
    'jombang': [-7.5461, 112.2331],
    'lumajang': [-8.1333, 113.2247],
    'jember': [-8.1724, 113.7000],
    'bondowoso': [-7.9136, 113.8214],
    'situbondo': [-7.7064, 114.0058],
    'banyuwangi': [-8.2192, 114.3692],
    'bangkalan': [-7.0456, 112.7486],
    'sampang': [-7.1878, 113.2394],
    'pamekasan': [-7.1597, 113.4739],
    'sumenep': [-7.0167, 113.8667],

    # Sumatera
    'banda aceh': [5.5483, 95.3238],
    'aceh': [5.5483, 95.3238],
    'sabang': [5.8943, 95.3242],
    'lhokseumawe': [5.1801, 97.1408],
    'langsa': [4.4716, 97.9691],
    'meulaboh': [4.1447, 96.1264],
    'medan': [3.5952, 98.6722],
    'pematangsiantar': [2.9599, 99.0687],
    'binjai': [3.6003, 98.4854],
    'tebing tinggi': [3.3285, 99.1625],
    'tanjungbalai': [2.9667, 99.8000],
    'sibolga': [1.7426, 98.7792],
    'padangsidimpuan': [1.3734, 99.2734],
    'gunungsitoli': [1.2825, 97.6158],
    'kabanjahe': [3.1778, 98.4908],
    'lubuk pakam': [3.5600, 98.8800],
    'kisaran': [2.9833, 99.6167],
    'rantau prapat': [2.0967, 99.8278],
    'padang': [-0.9471, 100.4172],
    'bukittinggi': [-0.3056, 100.3692],
    'payakumbuh': [-0.2247, 100.6322],
    'solok': [-0.7984, 100.6539],
    'pariaman': [-0.6264, 100.1200],
    'padang panjang': [-0.4636, 100.3986],
    'sawahlunto': [-0.6806, 100.7817],
    'pekanbaru': [0.5071, 101.4478],
    'dumai': [1.6669, 101.4501],
    'duri': [1.2725, 101.2181],
    'bengkalis': [1.4822, 102.0792],
    'siak': [0.7997, 102.0494],
    'kampar': [0.3344, 101.0253],
    'bangkinang': [0.3344, 101.0253],
    'rengat': [-0.3756, 102.5456],
    'tembilahan': [-0.3167, 103.1500],
    'batam': [1.1301, 104.0529],
    'tanjungpinang': [0.9167, 104.4500],
    'tanjung balai karimun': [0.9926, 103.4281],
    'karimun': [0.9926, 103.4281],
    'bintan': [1.0000, 104.5000],
    'natuna': [3.9456, 108.1429],
    'ranai': [3.9456, 108.1429],
    'anambas': [3.2000, 106.2500],
    'jambi': [-1.6101, 103.6131],
    'sungai penuh': [-2.0622, 101.3939],
    'muaro jambi': [-1.5544, 103.8050],
    'muara bunggo': [-1.5000, 102.1167],
    'bangko': [-2.2000, 102.2667],
    'sarolangun': [-2.3000, 102.6500],
    'kuala tungkal': [-0.8167, 103.4667],
    'palembang': [-2.9761, 104.7754],
    'prabumulih': [-3.4357, 104.2341],
    'lubuklinggau': [-3.2964, 102.8617],
    'pagar alam': [-4.0279, 103.2678],
    'banyuasin': [-2.8833, 104.3833],
    'lahat': [-3.7833, 103.5333],
    'muara enim': [-3.6500, 103.7667],
    'baturaja': [-4.1333, 104.1667],
    'kayu agung': [-3.3833, 104.8333],
    'bengkulu': [-3.8004, 102.2655],
    'curup': [-3.4682, 102.5489],
    'rejang lebong': [-3.4682, 102.5489],
    'mukomuko': [-2.5833, 101.1167],
    'pangkalpinang': [-2.1316, 106.1119],
    'bangka': [-2.1316, 106.1119],
    'belitung': [-2.7358, 107.6358],
    'tanjung pandan': [-2.7358, 107.6358],
    'bandar lampung': [-5.4500, 105.2667],
    'lampung': [-5.4500, 105.2667],
    'metro': [-5.1136, 105.3067],
    'kalianda': [-5.7000, 105.6000],
    'lampung selatan': [-5.7000, 105.6000],
    'kotabumi': [-4.8333, 104.8833],

    # Bali & Nusa Tenggara
    'denpasar': [-8.6500, 115.2167],
    'bali': [-8.6500, 115.2167],
    'badung': [-8.5833, 115.1833],
    'kuta': [-8.7233, 115.1725],
    'gianyar': [-8.5442, 115.3286],
    'ubud': [-8.5069, 115.2625],
    'tabanan': [-8.5392, 115.1239],
    'singaraja': [-8.1120, 115.0882],
    'buleleng': [-8.1120, 115.0882],
    'mataram': [-8.5833, 116.1167],
    'lombok': [-8.5833, 116.1167],
    'bima': [-8.4608, 118.7267],
    'sumbawa': [-8.5000, 117.4333],
    'praya': [-8.7058, 116.2758],
    'kupang': [-10.1772, 123.6070],
    'ende': [-8.8431, 121.6622],
    'maumere': [-8.6199, 122.2111],
    'labuan bajo': [-8.4964, 119.8877],
    'ruteng': [-8.6136, 120.4639],
    'waingapu': [-9.6567, 120.2642],
    'kalabahi': [-8.2189, 124.5186],
    'alor': [-8.2189, 124.5186],
    'atambua': [-9.1078, 124.8925],

    # Kalimantan
    'pontianak': [-0.0263, 109.3425],
    'singkawang': [0.9067, 108.9856],
    'sambas': [1.3619, 109.3039],
    'ketapang': [-1.8483, 109.9753],
    'sintang': [0.0767, 111.4983],
    'palangkaraya': [-2.2078, 113.9164],
    'sampit': [-2.5333, 112.9500],
    'pangkalan bun': [-2.6833, 111.6167],
    'banjarmasin': [-3.3194, 114.5908],
    'banjarbaru': [-3.4400, 114.8300],
    'martapura': [-3.4111, 114.8556],
    'batulicin': [-3.4500, 115.9833],
    'kotabaru': [-3.2389, 116.2242],
    'samarinda': [-0.5022, 117.1536],
    'balikpapan': [-1.2379, 116.8529],
    'bontang': [0.1333, 117.5000],
    'tenggarong': [-0.4136, 116.9889],
    'kutai kartanegara': [-0.4136, 116.9889],
    'tanjung redeb': [2.1550, 117.4947],
    'berau': [2.1550, 117.4947],
    'sangatta': [0.4903, 117.5456],
    'tarakan': [3.3000, 117.6333],
    'tanjung selor': [2.8378, 117.3653],
    'nunukan': [4.1333, 117.6667],

    # Sulawesi
    'makassar': [-5.1477, 119.4327],
    'ujung pandang': [-5.1477, 119.4327],
    'parepare': [-4.0131, 119.6253],
    'palopo': [-2.9944, 120.1969],
    'gowa': [-5.2000, 119.4500],
    'maros': [-5.0000, 119.5833],
    'bone': [-4.5386, 120.3289],
    'watampone': [-4.5386, 120.3289],
    'manado': [1.4748, 124.8428],
    'bitung': [1.4404, 125.1840],
    'tomohon': [1.3200, 124.8400],
    'kotamobagu': [0.7306, 124.3139],
    'palu': [-0.8917, 119.8707],
    'luwuk': [-0.9517, 122.7875],
    'poso': [-1.3958, 120.7533],
    'kendari': [-3.9985, 122.5126],
    'baubau': [-5.4633, 122.6017],
    'kolaka': [-4.0500, 121.6000],
    'gorontalo': [0.5435, 123.0568],
    'mamuju': [-2.6770, 118.8895],

    # Maluku & Maluku Utara
    'ambon': [-3.6554, 128.1908],
    'tual': [-5.6300, 132.7500],
    'ternate': [0.7833, 127.3667],
    'tidore': [0.6833, 127.4000],
    'tobelo': [1.7333, 128.0000],

    # Papua All Regions
    'jayapura': [-2.5916, 140.6690],
    'sentani': [-2.5667, 140.4833],
    'biak': [-1.1739, 136.0825],
    'serui': [-1.8833, 136.2333],
    'manokwari': [-0.8615, 134.0620],
    'sorong': [-0.8762, 131.2558],
    'fakfak': [-2.9269, 132.2961],
    'kaimana': [-3.6667, 133.7667],
    'nabire': [-3.3667, 135.4833],
    'timika': [-4.5467, 136.8839],
    'mimika': [-4.5467, 136.8839],
    'wamena': [-4.0956, 138.9439],
    'jayawijaya': [-4.0956, 138.9439],
    'merauke': [-8.4991, 140.4011],
    'boven digoel': [-6.0833, 140.3000],
    'asmat': [-5.5333, 138.1333],
    'agats': [-5.5333, 138.1333],
}

# Major TLC Airport / Hub Code Coordinates
TLC_COORDINATES = {
    'CGK': [-6.1256, 106.6558], # Jakarta (Soekarno-Hatta)
    'HLP': [-6.2667, 106.8917], # Jakarta (Halim)
    'JKT': [-6.2088, 106.8456], # Jakarta
    'JKS': [-6.2615, 106.8106], # Jakarta Selatan
    'BKS': [-6.2383, 106.9756], # Bekasi
    'BDO': [-6.9006, 107.5761], # Bandung
    'SUB': [-7.3798, 112.7875], # Surabaya (Juanda)
    'SRG': [-6.9711, 110.3756], # Semarang (Ahmad Yani)
    'SOC': [-7.5161, 110.7569], # Solo (Adisumarmo)
    'JOG': [-7.7881, 110.4319], # Yogyakarta (Adisutjipto)
    'YIA': [-7.9042, 110.0578], # Yogyakarta (Kulon Progo)
    'MLG': [-7.9267, 112.7139], # Malang (Abdul Rachman Saleh)
    'DPS': [-8.7482, 115.1672], # Bali / Denpasar (Ngurah Rai)
    'LOP': [-8.7583, 116.2750], # Lombok (Praya)
    'KOE': [-10.1714, 123.6708], # Kupang (El Tari)
    'KNO': [3.6422, 98.8853],   # Medan (Kualanamu)
    'MES': [3.5581, 98.6850],   # Medan (Polonia)
    'BTJ': [5.5244, 95.4206],   # Banda Aceh (Sultan Iskandar Muda)
    'PDG': [-0.7869, 100.2806], # Padang (Minangkabau)
    'PKU': [0.4608, 101.4447],  # Pekanbaru (SSQ II)
    'BTH': [1.1211, 104.1189],  # Batam (Hang Nadim)
    'TNJ': [0.9236, 104.5317],  # Tanjungpinang
    'DJB': [-1.6381, 103.6442], # Jambi (Sultan Thaha)
    'PLM': [-2.8983, 104.7000], # Palembang (SMB II)
    'BKS_TLC': [-3.7800, 102.3400], # Bengkulu (Fatmawati)
    'BKG': [-3.7800, 102.3400], # Bengkulu
    'PGK': [-2.1625, 106.1392], # Pangkalpinang (Depati Amir)
    'TJQ': [-2.7558, 107.7539], # Belitung (H.A.S. Hanandjoeddin)
    'TKG': [-5.2422, 105.1783], # Lampung (Radin Inten II)
    'PNK': [-0.1506, 109.4039], # Pontianak (Supadio)
    'PKY': [-2.2250, 113.9439], # Palangkaraya (Tjilik Riwut)
    'BDJ': [-3.4472, 114.7575], # Banjarmasin (Syamsudin Noor)
    'BPN': [-1.2683, 116.8944], # Balikpapan (SAMS Sepinggan)
    'AAP': [-0.4858, 117.1578], # Samarinda (APT Pranoto)
    'TRK': [3.3267, 117.5678],  # Tarakan (Juwata)
    'UPG': [-5.0617, 119.5539], # Makassar (Sultan Hasanuddin)
    'MDC': [1.5492, 124.9261],  # Manado (Sam Ratulangi)
    'PLW': [-0.9181, 119.9097], # Palu (Mutiara SIS Al Jufri)
    'KDI': [-4.0817, 122.4181], # Kendari (Haluoleo)
    'GTO': [0.6372, 122.8519],  # Gorontalo (Djalaluddin)
    'MJU': [-2.5658, 118.9189], # Mamuju (Tampa Padang)
    'AMQ': [-3.7103, 128.0894], # Ambon (Pattimura)
    'TTE': [0.8314, 127.3808],  # Ternate (Sultan Babullah)
    'DJJ': [-2.5769, 140.5161], # Jayapura (Sentani)
    'SOQ': [-0.8925, 131.2872], # Sorong (DEO)
    'MKW': [-0.8758, 134.0506], # Manokwari (Rendani)
    'TIM': [-4.5286, 136.8869], # Timika (Mozes Kilangin)
    'MKQ': [-8.5203, 140.4178], # Merauke (Mopah)
    'WMX': [-4.0975, 138.9519], # Wamena
    'NBX': [-3.3667, 135.4967], # Nabire
    'BIK': [-1.1906, 136.1089], # Biak (Frans Kaisiepo)
}


def clean_location_name(name):
    """Normalize city or location name for dictionary lookup."""
    if not name:
        return ""
    text = str(name).strip().lower()
    # Remove prefix keywords
    text = re.sub(r'^(kota|kabupaten|kab\.|kab|provinsi|prov\.|daerah|wilayah|cabang|hub|gudang|branch)\s+', '', text).strip()
    return text


def get_coordinates_for_location(location_str, tlc_code=None):
    """
    Resolve [latitude, longitude] for any given location string or TLC code.
    Returns [lat, lng] or a sensible default [ -6.2088, 106.8456 ] (Jakarta).
    """
    # 1. Try matching TLC code directly if provided
    if tlc_code:
        tlc_clean = str(tlc_code).strip().upper()
        if tlc_clean in TLC_COORDINATES:
            return TLC_COORDINATES[tlc_clean]

    if not location_str:
        return [-6.2088, 106.8456]

    raw = str(location_str).strip()
    
    # Check if raw string contains TLC prefix like 'DJJ - Jayapura'
    if " - " in raw:
        parts = raw.split(" - ", 1)
        if len(parts[0].strip()) == 3 and parts[0].strip().isalpha():
            tlc_candidate = parts[0].strip().upper()
            if tlc_candidate in TLC_COORDINATES:
                return TLC_COORDINATES[tlc_candidate]
        raw = parts[1].strip()

    cleaned = clean_location_name(raw)

    # 2. Exact match in CITY_COORDINATES
    if cleaned in CITY_COORDINATES:
        return CITY_COORDINATES[cleaned]

    # 3. Partial / word boundary match
    for city_key, coords in CITY_COORDINATES.items():
        if city_key in cleaned or cleaned in city_key:
            return coords

    # 4. Check if location has coverage TLC in DB
    try:
        from apps.master.models import Coverage
        cov = Coverage.objects.filter(city__icontains=cleaned, is_active=True).exclude(tlc__isnull=True).exclude(tlc__exact='').first()
        if cov and cov.tlc and cov.tlc.upper() in TLC_COORDINATES:
            return TLC_COORDINATES[cov.tlc.upper()]
    except Exception:
        pass

    # Default fallback
    return [-6.2088, 106.8456]
