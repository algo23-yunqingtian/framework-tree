"""点击确定关闭"""
import json, requests, websocket, time

tabs = requests.get("http://127.0.0.1:9222/json").json()
ws = websocket.create_connection(tabs[0]["webSocketDebuggerUrl"], timeout=15)
mid = [1]
def c(m, p=None):
    ws.send(json.dumps({"id":mid[0],"method":m,"params":p or {}}))
    mid[0] += 1
    return json.loads(ws.recv())

# 找到确定按钮
r = c("Runtime.evaluate", {"expression": """
(function(){
    var els=document.querySelectorAll('*');
    for(var i=0;i<els.length;i++){
        var t=els[i].textContent.trim();
        if(t==='确定' || t==='确 定'){
            var rc=els[i].getBoundingClientRect();
            if(rc.width>0 && rc.width<200){
                return JSON.stringify({x:Math.round(rc.x+rc.width/2),y:Math.round(rc.y+rc.height/2)});
            }
        }
    }
    return 'NF';
})()"""})

raw = r.get('result',{}).get('result',{}).get('value','NF')

if raw != 'NF':
    v = json.loads(raw)
    c("Input.dispatchMouseEvent", {"type":"mouseMoved","x":v['x'],"y":v['y']})
    time.sleep(0.3)
    c("Input.dispatchMouseEvent", {"type":"mousePressed","x":v['x'],"y":v['y'],"button":"left","clickCount":1})
    time.sleep(0.3)
    c("Input.dispatchMouseEvent", {"type":"mouseReleased","x":v['x'],"y":v['y'],"button":"left","clickCount":1})
    time.sleep(3)
    
    r2 = c("Runtime.evaluate", {"expression":"window.location.href"})
    url = r2.get('result',{}).get('result',{}).get('value','')
    
    with open(r"D:\DSH_WORK\周报\_auto5_state.txt","w",encoding="utf-8") as f:
        f.write(f"URL: {url}")

ws.close()
