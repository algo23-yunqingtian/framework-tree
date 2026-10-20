"""答题Q2"""
import json, requests, websocket, time

def get_ws():
    return websocket.create_connection(requests.get("http://127.0.0.1:9222/json").json()[0]["webSocketDebuggerUrl"], timeout=15)

def click_option(text):
    ws = get_ws()
    mid = [1]
    def c(m, p=None):
        ws.send(json.dumps({"id":mid[0],"method":m,"params":p or {}}))
        mid[0] += 1
        return json.loads(ws.recv())
    r = c("Runtime.evaluate", {"expression": """
    (function(){
        var els=document.querySelectorAll('.answer-options.answer-format.rich-text-style');
        for(var i=0;i<els.length;i++){
            if(els[i].textContent.trim().indexOf('""" + text.replace("'","\\'") + """')!==-1){
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

def get_text():
    ws = get_ws()
    mid = [1]
    def c(m, p=None):
        ws.send(json.dumps({"id":mid[0],"method":m,"params":p or {}}))
        mid[0] += 1
        return json.loads(ws.recv())
    r = c("Runtime.evaluate", {"expression":"document.body.innerText"})
    text = r.get('result',{}).get('result',{}).get('value','')
    ws.close()
    return text

# Q2: C. 常
click_option("常")
js_next()
# Q3
text = get_text()
with open(r"D:\DSH_WORK\周报\_q_next2.txt","w",encoding="utf-8") as f:
    f.write(text[:400])
