"""检查状态"""
import json, requests, websocket

tabs = requests.get("http://127.0.0.1:9222/json").json()
ws = websocket.create_connection(tabs[0]["webSocketDebuggerUrl"], timeout=15)
mid = [1]
def c(m, p=None):
    ws.send(json.dumps({"id":mid[0],"method":m,"params":p or {}}))
    mid[0] += 1
    return json.loads(ws.recv())

r = c("Runtime.evaluate", {"expression":"document.body.innerText"})
text = r.get('result',{}).get('result',{}).get('value','')
ws.close()

with open(r"D:\DSH_WORK\周报\_current.txt","w",encoding="utf-8") as f:
    f.write(text[:400])
