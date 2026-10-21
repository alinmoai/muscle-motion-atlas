"""Traditional Chinese display names and functional groups for the muscles in the two regions.
NAME_FIX records names that are wrong in the source model (verified by position)."""

NAME_FIX = {
    # Z-Anatomy labels the upper and lower trapezius the wrong way round: the mesh called "Ascending part"
    # sits on the neck and runs to the clavicle (that is the upper/descending part), and vice versa.
    'Ascending part of trapezius muscle': 'Descending part of trapezius muscle',
    'Descending part of trapezius muscle': 'Ascending part of trapezius muscle',
}

ZH = {
    # ---- shoulder girdle / trunk-to-limb ----
    'Descending part of trapezius muscle': '斜方肌上束',
    'Transverse part of trapezius muscle': '斜方肌中束',
    'Ascending part of trapezius muscle': '斜方肌下束',
    'Latissimus dorsi muscle': '闊背肌',
    'Levator scapulae': '提肩胛肌',
    'Rhomboid major muscle': '大菱形肌',
    'Rhomboid minor muscle': '小菱形肌',
    'Serratus anterior muscle': '前鋸肌',
    'Pectoralis minor muscle': '胸小肌',
    'Subclavius muscle': '鎖骨下肌',
    'Clavicular head of pectoralis major muscle': '胸大肌 鎖骨頭',
    'Sternocostal head of pectoralis major muscle': '胸大肌 胸肋頭',
    '(Abdominal part of pectoralis major muscle)': '胸大肌 腹部',
    # ---- shoulder ----
    'Clavicular part of deltoid muscle': '三角肌 前束',
    'Acromial part of deltoid muscle': '三角肌 中束',
    'Scapular spinal part of deltoid muscle': '三角肌 後束',
    'Supraspinatus muscle': '棘上肌',
    'Infraspinatus muscle': '棘下肌',
    'Teres minor muscle': '小圓肌',
    'Subscapularis muscle': '肩胛下肌',
    'Teres major muscle': '大圓肌',
    'Coracobrachialis muscle': '喙肱肌',
    # ---- arm ----
    'Long head of biceps brachii': '肱二頭肌 長頭',
    'Short head of biceps brachii': '肱二頭肌 短頭',
    'Brachialis muscle': '肱肌',
    'Long head of triceps brachii': '肱三頭肌 長頭',
    'Lateral head of triceps brachii': '肱三頭肌 外側頭',
    'Medial head of triceps brachii': '肱三頭肌 內側頭',
    'Anconeus muscle': '肘肌',
    # ---- forearm, anterior ----
    'Superficial head of pronator teres': '旋前圓肌 淺頭',
    'Deep head of pronator teres': '旋前圓肌 深頭',
    'Flexor carpi radialis': '橈側屈腕肌',
    'Palmaris longus muscle': '掌長肌',
    'Humeral head of flexor carpi ulnaris': '尺側屈腕肌 肱骨頭',
    'Ulnar head of flexor carpi ulnaris': '尺側屈腕肌 尺骨頭',
    'Humero-ulnar head of flexor digitorum superficialis': '屈指淺肌 肱尺頭',
    'Radial head of flexor digitorum superficialis': '屈指淺肌 橈骨頭',
    'Flexor digitorum profundus': '屈指深肌',
    'Flexor pollicis longus': '屈拇長肌',
    'Pronator quadratus': '旋前方肌',
    # ---- forearm, posterior ----
    'Brachioradialis muscle': '肱橈肌',
    'Extensor carpi radialis longus': '橈側伸腕長肌',
    'Extensor carpi radialis brevis': '橈側伸腕短肌',
    'Extensor digitorum': '伸指肌',
    'Extensor digiti minimi': '伸小指肌',
    'Humeral head of extensor carpi ulnaris': '尺側伸腕肌 肱骨頭',
    'Ulnar head of extensor carpi ulnaris': '尺側伸腕肌 尺骨頭',
    'Supinator': '旋後肌',
    'Abductor pollicis longus': '外展拇長肌',
    'Extensor pollicis brevis': '伸拇短肌',
    'Extensor pollicis longus': '伸拇長肌',
    'Extensor indicis': '伸食指肌',
    # ---- hand ----
    'Abductor pollicis brevis': '外展拇短肌',
    'Superficial head of flexor pollicis brevis': '屈拇短肌 淺頭',
    'Deep head of flexor pollicis brevis': '屈拇短肌 深頭',
    'Opponens pollicis muscle': '拇對掌肌',
    'Oblique head of adductor pollicis': '內收拇肌 斜頭',
    'Transverse head of adductor pollicis': '內收拇肌 橫頭',
    'Abductor digiti minimi of hand': '外展小指肌',
    'Flexor digiti minimi of hand': '屈小指短肌',
    'Opponens digiti minimi muscle of hand': '小指對掌肌',
    'Lumbrical muscles of hand': '手部蚓狀肌',
    'Dorsal interossei muscles of hand': '手背側骨間肌',
    'Palmar interossei muscles': '掌側骨間肌',
    # ---- hip ----
    'Psoas major': '腰大肌',
    'Iliacus muscle': '髂肌',
    'Gluteus maximus muscle': '臀大肌',
    'Gluteus medius muscle': '臀中肌',
    'Gluteus minimus muscle': '臀小肌',
    'Tensor fasciae latae': '闊筋膜張肌',
    'Piriformis muscle': '梨狀肌',
    'Superior gemellus muscle': '上孖肌',
    'Inferior gemellus muscle': '下孖肌',
    'Obturator internus': '閉孔內肌',
    'Obturator externus': '閉孔外肌',
    'Quadratus femoris muscle': '股方肌',
    # ---- thigh ----
    'Sartorius muscle': '縫匠肌',
    'Rectus femoris muscle': '股直肌',
    'Vastus lateralis muscle': '股外側肌',
    'Vastus medialis muscle': '股內側肌',
    'Vastus intermedius muscle': '股中間肌',
    'Pectineus muscle': '恥骨肌',
    'Adductor longus': '內收長肌',
    'Adductor brevis': '內收短肌',
    'Adductor magnus': '內收大肌',
    '(Adductor minimus)': '內收小肌',
    'Gracilis muscle': '股薄肌',
    'Long head of biceps femoris': '股二頭肌 長頭',
    'Short head of biceps femoris': '股二頭肌 短頭',
    'Semitendinosus muscle': '半腱肌',
    'Semimembranosus muscle': '半膜肌',
    # ---- leg ----
    'Popliteus muscle': '膕肌',
    'Lateral head of gastrocnemius': '腓腸肌 外側頭',
    'Medial head of gastrocnemius': '腓腸肌 內側頭',
    'Soleus muscle': '比目魚肌',
    'Plantaris muscle': '蹠肌',
    'Calcaneal tendon': '跟腱（阿基里斯腱）',
    'Tibialis anterior muscle': '脛前肌',
    'Extensor digitorum longus': '伸趾長肌',
    'Tendon of extensor digitorum longus': '伸趾長肌 肌腱',
    'Extensor hallucis longus': '伸拇長肌（足）',
    'Fibularis tertius muscle': '第三腓骨肌',
    'Fibularis longus muscle': '腓骨長肌',
    'Fibularis brevis muscle': '腓骨短肌',
    'Tibialis posterior muscle': '脛後肌',
    'Flexor digitorum longus': '屈趾長肌',
    'Flexor hallucis longus': '屈拇長肌（足）',
    # ---- foot ----
    'Extensor digitorum brevis': '伸趾短肌',
    'Extensor hallucis brevis': '伸拇短肌（足）',
    'Abductor hallucis': '外展拇肌（足）',
    'Flexor digitorum brevis': '屈趾短肌',
    'Abductor digiti minimi of foot': '外展小趾肌',
    'Quadratus plantae muscle': '蹠方肌',
    'Lumbrical muscles of foot': '足部蚓狀肌',
    'Lateral head of flexor hallucis brevis': '屈拇短肌（足）外側頭',
    'Medial head of flexor hallucis brevis': '屈拇短肌（足）內側頭',
    'Oblique head of adductor hallucis': '內收拇肌（足）斜頭',
    'Transverse head of adductor hallucis': '內收拇肌（足）橫頭',
    'Flexor digiti minimi of foot': '屈小趾短肌',
    '(Opponens digiti minimi muscle of foot)': '小趾對掌肌',
    'Dorsal interossei muscles of foot': '足背側骨間肌',
    'Plantar interossei muscles': '蹠側骨間肌',
}

# functional groups shown in the viewer (order = display order)
GROUPS = {
    'arm': [
        ('girdle', '肩胛帶（軀幹到肩胛／鎖骨）', ['Descending part of trapezius muscle', 'Transverse part of trapezius muscle',
            'Ascending part of trapezius muscle', 'Levator scapulae', 'Rhomboid major muscle', 'Rhomboid minor muscle',
            'Serratus anterior muscle', 'Pectoralis minor muscle', 'Subclavius muscle']),
        ('shoulder', '肩關節（到肱骨）', ['Clavicular part of deltoid muscle', 'Acromial part of deltoid muscle',
            'Scapular spinal part of deltoid muscle', 'Clavicular head of pectoralis major muscle',
            'Sternocostal head of pectoralis major muscle', '(Abdominal part of pectoralis major muscle)',
            'Latissimus dorsi muscle', 'Teres major muscle', 'Coracobrachialis muscle']),
        ('cuff', '旋轉肌袖', ['Supraspinatus muscle', 'Infraspinatus muscle', 'Teres minor muscle', 'Subscapularis muscle']),
        ('arm', '上臂', ['Long head of biceps brachii', 'Short head of biceps brachii', 'Brachialis muscle',
            'Long head of triceps brachii', 'Lateral head of triceps brachii', 'Medial head of triceps brachii', 'Anconeus muscle']),
        ('flexors', '前臂 屈肌側（掌側）', ['Superficial head of pronator teres', 'Deep head of pronator teres', 'Flexor carpi radialis',
            'Palmaris longus muscle', 'Humeral head of flexor carpi ulnaris', 'Ulnar head of flexor carpi ulnaris',
            'Humero-ulnar head of flexor digitorum superficialis', 'Radial head of flexor digitorum superficialis',
            'Flexor digitorum profundus', 'Flexor pollicis longus', 'Pronator quadratus']),
        ('extensors', '前臂 伸肌側（背側）', ['Brachioradialis muscle', 'Extensor carpi radialis longus', 'Extensor carpi radialis brevis',
            'Extensor digitorum', 'Extensor digiti minimi', 'Humeral head of extensor carpi ulnaris', 'Ulnar head of extensor carpi ulnaris',
            'Supinator', 'Abductor pollicis longus', 'Extensor pollicis brevis', 'Extensor pollicis longus', 'Extensor indicis']),
        ('hand', '手內在肌', ['Abductor pollicis brevis', 'Superficial head of flexor pollicis brevis', 'Deep head of flexor pollicis brevis',
            'Opponens pollicis muscle', 'Oblique head of adductor pollicis', 'Transverse head of adductor pollicis',
            'Abductor digiti minimi of hand', 'Flexor digiti minimi of hand', 'Opponens digiti minimi muscle of hand',
            'Lumbrical muscles of hand', 'Dorsal interossei muscles of hand', 'Palmar interossei muscles']),
    ],
    'leg': [
        ('hipflex', '髖前側（屈髖）', ['Psoas major', 'Iliacus muscle', 'Tensor fasciae latae', 'Sartorius muscle', 'Rectus femoris muscle']),
        ('glute', '臀部與深層外旋肌', ['Gluteus maximus muscle', 'Gluteus medius muscle', 'Gluteus minimus muscle', 'Piriformis muscle',
            'Superior gemellus muscle', 'Inferior gemellus muscle', 'Obturator internus', 'Obturator externus', 'Quadratus femoris muscle']),
        ('quad', '大腿前側（股四頭肌）', ['Vastus lateralis muscle', 'Vastus medialis muscle', 'Vastus intermedius muscle']),
        ('adductor', '大腿內側（內收肌群）', ['Pectineus muscle', 'Adductor longus', 'Adductor brevis', 'Adductor magnus',
            '(Adductor minimus)', 'Gracilis muscle']),
        ('hamstring', '大腿後側（膕旁肌）', ['Long head of biceps femoris', 'Short head of biceps femoris', 'Semitendinosus muscle',
            'Semimembranosus muscle']),
        ('calf', '小腿後側', ['Lateral head of gastrocnemius', 'Medial head of gastrocnemius', 'Soleus muscle', 'Plantaris muscle',
            'Calcaneal tendon', 'Popliteus muscle', 'Tibialis posterior muscle', 'Flexor digitorum longus', 'Flexor hallucis longus']),
        ('shin', '小腿前側與外側', ['Tibialis anterior muscle', 'Extensor digitorum longus', 'Tendon of extensor digitorum longus',
            'Extensor hallucis longus', 'Fibularis tertius muscle', 'Fibularis longus muscle', 'Fibularis brevis muscle']),
        ('foot', '足內在肌', ['Extensor digitorum brevis', 'Extensor hallucis brevis', 'Abductor hallucis', 'Flexor digitorum brevis',
            'Abductor digiti minimi of foot', 'Quadratus plantae muscle', 'Lumbrical muscles of foot',
            'Lateral head of flexor hallucis brevis', 'Medial head of flexor hallucis brevis', 'Oblique head of adductor hallucis',
            'Transverse head of adductor hallucis', 'Flexor digiti minimi of foot', '(Opponens digiti minimi muscle of foot)',
            'Dorsal interossei muscles of foot', 'Plantar interossei muscles']),
    ],
}

BONE_ZH = {
    'Clavicle': '鎖骨', 'Scapula': '肩胛骨', 'Humerus': '肱骨', 'Ulna': '尺骨', 'Radius': '橈骨',
    'Scaphoid bone': '舟狀骨', 'Lunate bone': '月狀骨', 'Triquetrum bone': '三角骨', 'Pisiform bone': '豌豆骨',
    'Trapezium bone': '大多角骨', 'Trapezoid bone': '小多角骨', 'Capitate bone': '頭狀骨', 'Hamate bone': '鉤狀骨',
    'Femur': '股骨', 'Patella': '髕骨', 'Tibia': '脛骨', 'Fibula': '腓骨', 'Talus': '距骨', 'Calcaneus': '跟骨',
    'Navicular bone': '舟狀骨（足）', 'Cuboid bone': '骰骨', 'Medial cuneiform bone': '內側楔狀骨',
    'Intermediate cuneiform bone': '中間楔狀骨', 'Lateral cuneiform bone': '外側楔狀骨', 'Sesamoid bones of foot': '籽骨',
    'Hip bone': '髖骨', 'Sacrum': '薦骨', 'Coccyx': '尾骨',
}
ORD = {'First': '第一', 'Second': '第二', 'Third': '第三', 'Fourth': '第四', 'Fifth': '第五',
       'first': '第一', 'second': '第二', 'third': '第三', 'fourth': '第四', 'fifth': '第五'}

def bone_zh(name):
    import re
    b = re.sub(r'\.(r|l)$', '', name)
    if b in BONE_ZH:
        return BONE_ZH[b]
    m = re.match(r'(First|Second|Third|Fourth|Fifth) (metacarpal|metatarsal) bone', b)
    if m:
        return f"{ORD[m.group(1)]}{'掌骨' if m.group(2) == 'metacarpal' else '蹠骨'}"
    m = re.match(r'(Proximal|Middle|Distal) phalanx of (\w+) finger of (hand|foot)', b)
    if m:
        p = {'Proximal': '近節', 'Middle': '中節', 'Distal': '遠節'}[m.group(1)]
        f = {'hand': '指', 'foot': '趾'}[m.group(3)]
        return f"{ORD[m.group(2)]}{f}{p}{'指骨' if m.group(3) == 'hand' else '趾骨'}"
    m = re.match(r'(.*) rib', b)
    if m:
        return '肋骨'
    if b.startswith('Vertebra') or b.startswith('Atlas') or b.startswith('Axis'):
        return '脊椎 ' + b.replace('Vertebra ', '').replace('Atlas (C1)', 'C1').replace('Axis (C2)', 'C2')
    return b
