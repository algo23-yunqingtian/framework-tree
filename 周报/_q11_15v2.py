"""答题Q11-Q15并提交"""
import json, requests, websocket, time

def get_ws():
    return websocket.create_connection(requests.get("http://127.0.0.1:9222/json").json()[0]["webSocketDebuggerUrl"], timeout=15)

def click_judge(text):
    ws = get_ws()
    mid = [1]
    def c(m, p=None):
        ws.send(json.dumps({"id":mid[0],"method":m,"params":p or {}}))
        mid[0] += 1
        return json.loads(ws.recv())
    r = c("Runtime.evaluate", {"expression": """
    (function(){
        var els=document.querySelectorAll('span.pointer.no-select');
        for(var i=0;i<els.length;i++){
            if(els[i].textContent.trim()==='""" + text + """'){
                var rc=els[i].getBoundingClientRect();
                return JSON.stringify({x:Math.round(rc.x+rc.width/2),y:Math.round(rc.y+rc.height/2)});
            }
        }
        return 'NF';
    })()"""})
    raw = r.get('result',{}).get('result',{}).get('value','NF')
    ws.close()
    if raw == 'NF': return False
    v = json.loads(raw)
    ws = get_ws()
    mid = [1]
    def c2(m, p=None):
        ws.send(json.dumps({"id":mid[0],"method":m,"params":p or {}}))
        mid[0] += 1
        return json.loads(ws.recv())
    c2("Input.dispatchMouseEvent", {"type":"mouseMoved","x":v['x'],"y":v['y']})
    time.sleep(0.2)
    c2("Input.dispatchMouseEvent", {"type":"mousePressed","x":v['x'],"y":v['y'],"button":"left","clickCount":1})
    time.sleep(0.2)
    c2("Input.dispatchMouseEvent", {"type":"mouseReleased","x":v['x'],"y":v['y'],"button":"left","clickCount":1})
    time.sleep(1.5)
    ws.close()
    return True

def js_next():
    ws = get_ws()
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
    ws.close()

# Q11: 正确
click_judge("正确")
js_next()
# Q12: 正确
click_judge("正确")
js_next()
# Q13: 正确
click_judge("正确")
js_next()
# Q14: 正确
click_judge("正确")
js_next()
# Q15: 正确
click_judge("正确")

# 提交
ws = get_ws()
mid = [1]
def c(m, p=None):
    ws.send(json.dumps({"id":mid[0],"method":m,"params":p or {}}))
    mid[0] += 1
    return json.loads(ws.recv())

r = c("Runtime.evaluate", {"expression": """
(function(){
    var els=document.querySelectorAll('div,button,a,span');
    for(var i=0;i<els.length;i++){
        if(els[i].textContent.trim()==='我要交卷'){
            var rc=els[i].getBoundingClientRect();
            return JSON.stringify({x:Math.round(rc.x+rc.width/2),y:Math.round(rc.y+rc.height/2)});
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
    time.sleep(2)
    
    r2 = c("Runtime.evaluate", {"expression": """
    (function(){
        var els=document.querySelectorAll('div,button,span');
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
    raw2 = r2.get('result',{}).get('result',{}).get('value','NF')
    
    if raw2 != 'NF':
        v2 = json.loads(raw2)
        c("Input.dispatchMouseEvent", {"type":"mouseMoved","x":v2['x'],"y":v2['y']})
        time.sleep(0.3)
        c("Input.dispatchMouseEvent", {"type":"mousePressed","x":v2['x'],"y":v2['y'],"button":"left","clickCount":1})
        time.sleep(0.3)
        c("Input.dispatchMouseEvent", {"type":"mouseReleased","x":v2['x'],"y":v2['y'],"button":"left","clickCount":1})
        time.sleep(3)
    
    r3 = c("Runtime.evaluate", {"expression":"document.body.innerText"})
    text = r3.get('result',{}).get('result',{}).get('value','')
    
    with open(r"D:\DSH_WORK\周报\_submit_result.txt","w",encoding="utf-8") as f:
        f.write(f"Submit: {'交卷成功' in text}")

ws.close()
