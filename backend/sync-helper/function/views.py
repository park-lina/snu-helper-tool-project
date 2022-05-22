from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from os import scandir, path, sep

from chromium.models import *
from config.error import *

from readfunc.readfunc import read_function_code

def comp(code, i, e, CODE):
    while i < e:
        if code == CODE[i]:
            return i
        i += 1
    return None

# Create your views here.
class FunctionViewSet(viewsets.GenericViewSet):

    # GET /functions/{function_name}/later
    @action(detail=True, methods=['GET'], url_path='later')
    def later(self, request, pk):
        fname = pk.split("::")[-1]
        path = request.query_params.get('path')
        file_extension = path.split('.')[-1]
        later_version = request.query_params.get('later_version')
        target_version = Chromium.target_version
        ROOT = Chromium.chromium_repo

        os.chdir(ROOT)
        msg = os.popen(f"git log {target_version}..{later_version} -L:{fname}:{path}").read()
        CODE_T = [''] + os.popen(f"git show {target_version}:{path}").read().split('\n')
        CODE_L = [''] + os.popen(f"git show {later_version}:{path}").read().split('\n')

        F2L_T = read_function_code(CODE_T, file_extension)
        F2L_L = read_function_code(CODE_L, file_extension)

        data = {"name": fname, "path": path, "target_version": target_version, "later_version": later_version}

        s1 = e1 = -1
        for i in range(1, len(CODE_T)):
            if fname in F2L_T[i]:
                s1 = e1 = i
                while e1 + 1 < len(CODE_T) and fname in F2L_T[e1+1]:
                    e1 += 1
                break

        s2 = e2 = -1
        for i in range(1, len(CODE_L)):
            if fname in F2L_L[i]:
                s2 = e2 = i
                while e2 + 1 < len(CODE_L) and fname in F2L_L[e2+1]:
                    e2 += 1
                break

        target_version_code = []
        later_version_code = []

        l1 = s1
        l2 = s2
        idx = 0
        while l1 <= e1 or l2 <= e2:
            if l1 <= e1 and l2 <= e2 and CODE_T[l1] == CODE_L[l2]:
                target_version_code.append({"index": idx, "line": l1, "content": CODE_T[l1], "type": "no change"})
                later_version_code.append({"index": idx, "line": l2, "content": CODE_L[l2], "type": "no change"})
                l1 += 1
                l2 += 1
                idx += 1
            else:
                nxt1 = comp(CODE_L[l2], l1, e1, CODE_T)
                if nxt1 != None:
                    while l1 < nxt1:
                        target_version_code.append({"index": idx, "line": l1, "content": CODE_T[l1], "type": "deleted"})
                        later_version_code.append({"index": idx, "line": 0, "content": "", "type": "none"})
                        l1 += 1
                        idx += 1
                    continue
                
                nxt2 = comp(CODE_T[l1], l2, e2, CODE_L)
                if nxt2 != None:
                    while l2 < nxt2:
                        target_version_code.append({"index": idx, "line": 0, "content": "", "type": "none"})
                        later_version_code.append({"index": idx, "line": l2, "content": CODE_L[l2], "type": "inserted"})
                        l2 += 1
                        idx += 1
                    continue
                
                target_version_code.append({"index": idx, "line": l1, "content": CODE_T[l1], "type": "deleted"})
                later_version_code.append({"index": idx, "line": l2, "content": CODE_L[l2], "type": "inserted"})
                l1 += 1
                l2 += 1
                idx += 1

        data["target_version_code"] = target_version_code
        data["later_version_code"] = later_version_code

        if msg == "":
            # no change
            data["comment"] = "no change"
        else:

            commits = msg.split("\n\ncommit ")
            
            for cmsg in commits:
                commit_id = cmsg.split("\n")[0].replace("commit ", "")

        return Response(data, status=status.HTTP_200_OK)