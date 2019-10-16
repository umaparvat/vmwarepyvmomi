from datetime import datetime
import re
import json
from pyVmomi.VmomiSupport import Object, DataObject, F_LINK, F_LINKABLE, F_OPTIONAL, F_SECRET, ManagedObject, PY3
from pyVmomi.VmomiSupport import UncallableManagedMethod, ManagedMethod, binary, GetVmodlType
from pyVmomi.Iso8601 import ParseISO8601
class MyJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
    def call_dict(self, val):
        print(f"val is {val}, type:{type(val)}")
        if isinstance(val, dict):
            if val.get("_vimtype"):
                if val.get("_moId"):
                    moId = val.pop("_vimId")
                    if val.get("serverGuid"):
                        serverGuid = val.pop("serverGuid")
                        sub_ins = GetVmodlType(val.pop("_vimtype"))(moId=moId, serverGuid=serverGuid)
                    else:
                        sub_ins = GetVmodlType(val.pop("_vimtype"))(moId=moId)
                else:
                    sub_ins = GetVmodlType(val.pop("_vimtype"))()
                for k,v in val.items():
                    cust_type = sub_ins._GetPropertyInfo(k).type
                    if isinstance(v, dict):
                        setattr(sub_ins, k, cust_type(self.call_dict(v)))
                    if isinstance(v, list):
                        if not v:
                            setattr(sub_ins, k, cust_type())
                        else:
                            mylocal_list = []
                            for each_item in v:
                                print(f"in v list {each_item}")
                                res=self.call_dict(each_item)
                                print(res)
                                mylocal_list.append(res)
                            setattr(sub_ins, k, cust_type(mylocal_list))
                    else:
                        print(f"cust type is {cust_type}")
                        ct = issubclass(cust_type, binary)
                        print(f"ct is {ct}")
                        if issubclass(cust_type, datetime):
                            print(f"i'm in datetime")
                            setattr(sub_ins, k, ParseISO8601(v))
                        elif issubclass(cust_type, binary):
                            print(f"i'm in binary, {k},{v}")
                            if PY3:
                                v = str.encode(v)
                            data_encode = base64.b64decode(v)
                            setattr(sub_ins, k, cust_type(data_encode))
                            print(f"i'm done")
                        elif issubclass(cust_type, type):
                            setattr(sub_ins, k, cust_type(v))
                        elif issubclass(cust_type, ManagedObject):
                            if isinstance(v, str):
                                mob = v.split(":")
                                print(f"mob {mob}")
                                if len(mob) == 3:
                                    mo_obj, serverGuid, moId = mob
                                    mo_ins = GetVmodlType(mo_obj)(moId=moId, serverGuid=serverGuid)
                                else:
                                    mo_obj,moId = mob
                                    mo_ins = GetVmodlType(mo_obj)(moId=moId)
                            else:
                                mo_ins = self.call_dict(v)
                            print(f"mo_ins {mo_ins}")
                            setattr(sub_ins, k, mo_ins)
                        else:
                            print(f"in else k:{k},v:{v}, cust_type:{cust_type}")
                            setattr(sub_ins, k, v)
                return sub_ins
        if isinstance(val, list):
            myins_list = []
            for each_item in val:
                print(f"val in list {each_item}")
                myins_list.append(self.call_dict(each_item))
            return myins_list
    def object_hook(self, our_dict):
        obj = self.call_dict(our_dict)
        return obj