if(!self.define){let e,a={};const i=(i,n)=>(i=new URL(i+".js",n).href,a[i]||new Promise((a=>{if("document"in self){const e=document.createElement("script");e.src=i,e.onload=a,document.head.appendChild(e)}else e=i,importScripts(i),a()})).then((()=>{let e=a[i];if(!e)throw new Error(`Module ${i} didn’t register its module`);return e})));self.define=(n,r)=>{const s=e||("document"in self?document.currentScript.src:"")||location.href;if(a[s])return;let c={};const f=e=>i(e,s),d={module:{uri:s},exports:c,require:f};a[s]=Promise.all(n.map((e=>d[e]||f(e)))).then((e=>(r(...e),c)))}}define(["./workbox-e3490c72"],(function(e){"use strict";self.addEventListener("message",(e=>{e.data&&"SKIP_WAITING"===e.data.type&&self.skipWaiting()})),e.precacheAndRoute([{url:"404.html",revision:"daac053b60ad5e8a5aa7ef36a7f871d1"},{url:"assets/index-BwTHU6Q8.js",revision:null},{url:"assets/index-C1C2dgbg.css",revision:null},{url:"index.html",revision:"315c8b62f8f5c6f41ff9cd2c67c060dc"},{url:"registerSW.js",revision:"1872c500de691dce40960bb85481de07"},{url:"logo.ico",revision:"3a4ec9b9245eac502ad8328b57da6bc0"},{url:"pwa-1024x1024.png",revision:"9da299ae0e97967a83e63434a50bdadb"},{url:"pwa-114x114.png",revision:"e95cde529a7f853e0a7e1b86c63c137b"},{url:"pwa-120x120.png",revision:"89168635fe45a4d8d4f4a1aa4f265795"},{url:"pwa-180x180.png",revision:"7f5021ea6002c2a85d609fb7504f0634"},{url:"pwa-192x192.png",revision:"be81ab9f27d955ee733af7af1777d5af"},{url:"pwa-29x29.png",revision:"2230745832c80e0b74278fb2847f2ef5"},{url:"pwa-40x40.png",revision:"d363780a27b54762cf7be8bb75a4224c"},{url:"pwa-512x512.png",revision:"79ffa82e911043b463b2e93cb75b9c6a"},{url:"pwa-57x57.png",revision:"f81c3696a3bb4183d7396758a3c6162f"},{url:"pwa-58x58.png",revision:"faca5d4cf906a17a915afa167a3e5fc1"},{url:"pwa-60x60.png",revision:"ad4eb12d00e1c0b12d6ba4948c6f0a1d"},{url:"pwa-80x80.png",revision:"d7f913aa6febe6ae55452fc13ccde208"},{url:"pwa-87x87.png",revision:"2d32e94c931e48f48a41685d0972c39c"},{url:"manifest.webmanifest",revision:"93957b607e991bc3ec8723d97a20bf47"}],{}),e.cleanupOutdatedCaches(),e.registerRoute(new e.NavigationRoute(e.createHandlerBoundToURL("index.html")))}));
