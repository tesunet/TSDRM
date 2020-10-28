from .models import *
import pymysql
from django.db import transaction


class DataMigrate(object):
    """
    迁移TSDRM->TSDRMV2
    """
    def __init__(self, credit:dict) -> None:
        """
        初始化连接
        @param conn: mysql数据库认证信息
        """
        self.msg = ""
        self.connection = None
        self.process_map = {
            12: 7,     # 另类投资 17
            13: 8,     # 投资交易 13
            14: 9,     # 资产估值 14
            15: 10,     # 办公审批 28
            17: 6,     # TA直销 12
        }
        # 新旧表Step ID对应关系
        self.step_map = {
            # 另类投资
            9: 127,
            10: 137,
            11: 148,
            12: 150,
            13: 151,
            14: 152,
            15: 153,
            16: 154,
            17: 155,
            18: 156,
            19: 157,
            20: 158,
            21: 161,
            22: 162,
            23: 163,
            24: 165,
            25: 166,
            188: 159,
            189: 160,
            191: 164,
            194: 149,

            # 投资交易
            104: 104,
            105: 139,
            106: 167,
            107: 171,
            108: 172,
            109: 174,
            110: 175,
            132: 173,
            133: 176,
            134: 177,
            135: 178,
            136: 179,
            137: 169,
            138: 170,
            139: 180,
            140: 181,
            141: 183,
            142: 182,
            143: 184,
            144: 185,
            195: 169,

            # 资产估值
            145: 128,
            146: 129,
            147: 186,
            148: 188,
            149: 189,
            150: 190,
            151: 191,
            152: 192,
            153: 193,
            154: 194,
            155: 195,
            156: 196,
            157: 197,
            158: 198,
            160: 199,
            161: 200,
            162: 201,
            163: 202,
            164: 203,
            165: 204,
            196: 187,

            # 办公审批
            166: 205,
            167: 206,
            168: 207,
            169: 209,
            170: 210,
            171: 211,
            172: 212,
            173: 213,
            174: 214,
            175: 215,
            176: 216,
            177: 217,
            178: 218,
            179: 219,
            181: 220,
            182: 221,
            183: 222,
            185: 223,
            186: 224,
            187: 225,
            197: 208,

            # TA直销 17-12
            111: 9,
            112: 14,
            113: 15,
            114: 140,
            115: 10,
            116: 17,
            117: 18,
            118: 19,
            119: 20,
            120: 136,
            121: 141,
            122: 11,
            124: 21,
            125: 13,
            126: 22,
            127: 143,
            128: 144,
            129: 145,
            130: 146,
            131: 147,
            193: 142,
        }

        # 新旧表ScriptInstance ID对应关系 scriptrun.id都一致 将pre.script_id <>  aft.scriptinstance_id
        self.scriptinstance_map = {
            # TA直销
            135: 45,
            136:46,
            137:47,
            138: 48,
            139:49,
            140:50,
            141:51,
            173:52,
            174:53,
            144:54,
            145:55,
            146:56,
            147:57,
            245:58,
            246:59,
            247:60,
            248:61,
            148:62,
            149:63,
            150:64,
            151:65,
            152:66,
            253:67,
            # 另类投资
            238:68,
            239:69,
            240:70,
            219:71,
            220:72,
            221:73,
            222:74,
            223:75,
            224:76,
            225:77,
            226:78,
            227:79,
            228:80,
            51:81,
            52:82,
            229:83,
            230:84,
            231:85,
            232:86,
            233:87,
            # 投资交易
            153:88,
            156:89,
            157:90,
            158:91,
            159:92,
            160:93,
            161:94,
            175:95,
            176:96,
            164:97,
            165:98,
            166:99,
            167:100,
            241:101,
            242:102,
            251:103,
            252:104,
            244:105,
            243:106,
            168:107,
            170:108,
            169:109,
            171:110,
            172:111,
            254:112,
            # 资产估值
            177:113,
            180:114,
            181:115,
            182:116,
            183:117,
            184:118,
            185:119,
            186:120,
            187:121,
            189:122,
            188:123,
            190:124,
            191:125,
            236:126,
            237:127,
            192:128,
            193:129,
            194:130,
            195:131,
            196:132,
            255:133,
            # 办公审批
            197:134,
            198:135,
            199:136,
            200:137,
            201:138,
            202:139,
            203:140,
            204:141,
            205:142,
            206:143,
            207:144,
            208:145,
            209:146,
            250:147,
            249:148,
            210:149,
            211:150,
            212:151,
            213:152,
            214:153,
        }

        try:
            self.connection = pymysql.connect(
                host=credit['host'],
                user=credit['user'],
                password=credit['passwd'],
                db=credit['db'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        except Exception as e:
            self.msg = "连接数据库失败"
    
    def fetch_all(self, sql) -> list:
        result = []
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
        return result

    @property
    def steprun_data(self) -> list:
        sql = """
        SELECT id, step_id
        FROM faconstor_steprun
        """
        return self.fetch_all(sql)

    @property
    def scriptrun_data(self) -> list:
        sql = """
        SELECT id, script_id
        FROM faconstor_scriptrun
        """
        return self.fetch_all(sql)

    def _migrate_steprun(self) -> bool:
        """
        迁移表StepRun
        """
        status = True
        stp_data = self.steprun_data

        try:
            with transaction.atomic():
                for sd in stp_data:
                    id = sd['id']
                    step_id = self.step_map.get(sd['step_id'], "")
                    StepRun.objects.filter(id=id).update(**{
                        "step_id": step_id,
                    })
        except Exception as e:
            print(e)
            status = False
            self.msg = e
        return status

    def _migrate_scriptrun(self) -> bool:
        """
        迁移表ScriptRun
        """
        status = True
        srt_data = self.scriptrun_data
        try:
            with transaction.atomic():
                for sd in srt_data:
                    id = sd['id']
                    script_id = self.scriptinstance_map.get(sd['script_id'], "")
                    ScriptRun.objects.filter(id=id).update(**{
                        "script_id": script_id,
                    })
        except Exception as e:
            print(e)
            status = False
            self.msg = e
        return status

    def migrate(self) -> bool:
        status = True
        # status = self._migrate_steprun()
        status = self._migrate_scriptrun()
        return status


if __name__ == "__main__":
    # 原数据库
    credit = {
        "host": "127.0.0.1",
        "user": "root",
        "passwd": "Passw0rD",
        "db": "pre",
    }

    m = DataMigrate(credit)
    m.migrate()