"""检查交卷状态"""
import json, requests, websocket, time

tabs = requests.get("http://127.0.0.1:9222/json").json()
ws = websocket.create_connection(tabs[0]["webSocketDebuggerUrl"], timeout=15)
mid = [1]
def c(m, p=None):
    ws.send(json.dumps({"id":mid[0],"method":m,"params":p or {}}))
    mid[0] += 1
    return json.loads(ws.recv())

# 查找交卷成功或确定按钮
r = c("Runtime.evaluate", {"expression": """
(function(){
    var text = document.body.innerText;
    var hasSuccess = text.indexOf('交卷成功') !== -1;
    var hasConfirm = text.indexOf('确定') !== -1;
    return JSON.stringify({hasSuccess:hasSuccess, hasConfirm:hasConfirm, hasSubmit:text.indexOf('我要交卷') !== -1});
})()"""})

raw = r.get('result',{}).get('result',{}).get('value','{}')
ws.close()

with open(r"D:\DSH_WORK\周报\_submit_status.txt","w",encoding="utf-8") as f:
    f.write(raw)
