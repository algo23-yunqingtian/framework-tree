"""点击下一题"""
import json, requests, websocket, time

tabs = requests.get("http://127.0.0.1:9222/json").json()
ws = websocket.create_connection(tabs[0]["webSocketDebuggerUrl"], timeout=15)
mid = [1]
def c(m, p=None):
    ws.send(json.dumps({"id":mid[0],"method":m,"params":p or {}}))
    mid[0] += 1
    return json.loads(ws.recv())

c("Runtime.evaluate", {"expression": """
(function(){
    var els=document.querySelectorAll('div,button,a,span');
    for(var i=0;i<els.length;i++){
        if(els[i].textContent.trim()==='下一题'){els[i].click();return}
    }
})()"""})
time.sleep(2)

r = c("Runtime.evaluate", {"expression":"document.body.innerText"})
text = r.get('result',{}).get('result',{}).get('value','')
ws.close()

with open(r"D:\DSH_WORK\周报\_q_next2.txt","w",encoding="utf-8") as f:
    f.write(text[:400])
