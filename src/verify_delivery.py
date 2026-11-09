"""Rebuild reproducibility, server smoke test, and optional browser screenshot."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,urllib.request
ROOT=Path(__file__).resolve().parents[1]
def main():
    def hashes(): return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['data/exports','outputs'] for p in sorted((ROOT/folder).glob('*.csv'))}
    before=hashes(); subprocess.run([sys.executable,'-m','src.build'],cwd=ROOT,check=True); after=hashes()
    result={'identical':before==after,'files_checked':len(after),'changed':[k for k in after if before.get(k)!=after[k]]}
    (ROOT/'outputs/reproducibility.json').write_text(json.dumps(result,indent=2)); assert result['identical']
    log=(ROOT/'outputs/streamlit.log').open('w')
    p=subprocess.Popen([sys.executable,'-m','streamlit','run','app.py','--server.headless=true','--server.port=8507','--browser.gatherUsageStats=false'],cwd=ROOT,stdout=log,stderr=log)
    status={'apptest':'All five pages and scenario input mutation exercised by pytest','server_health':False,'screenshot':False}
    try:
        for _ in range(30):
            try:
                with urllib.request.urlopen('http://localhost:8507/_stcore/health',timeout=2) as response: status['server_health']=response.read().decode()=='ok'
                break
            except Exception: time.sleep(.5)
        assert status['server_health']
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser=pw.chromium.launch(channel='msedge',headless=True)
                page=browser.new_page(viewport={'width':1440,'height':1100})
                page.goto('http://localhost:8507')
                page.get_by_test_id('stDataFrame').wait_for(timeout=30000)
                page.wait_for_timeout(1500)
                page.screenshot(path=str(ROOT/'outputs/app_overview.png'),full_page=True)
                browser.close(); status['screenshot']=True
        except Exception as ex: status['screenshot_limitation']=str(ex)[:400]
    finally: p.terminate(); p.wait(timeout=10); log.close()
    (ROOT/'outputs/app_validation.json').write_text(json.dumps(status,indent=2))
    print(json.dumps({'reproducibility':result,'app':status},indent=2))
if __name__=='__main__': main()
