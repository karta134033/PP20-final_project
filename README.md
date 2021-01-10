# 網路爬蟲效能優化應用

## 運行的實驗環境:
CPU: 
* Intel(R) Core(TM) i7-10700 CPU 基本速度:  2.90 GHz
* 核心數目:  8
* 邏輯處理器:  16

作業系統: ubuntu-20.04
程式語言: python 3.8.5

## python相關套件
* ray==1.0.1.post1
* beautifulsoup4==4.9.3
* fake-useragent==0.1.11

## 警告
執行各個程式請避免在短時間內重複執行，避免IP被鎖，建議間隔時間為5分鐘。

## 方法
比較的方法有三種: multiprocessing, threading, ray。
比較的方式依序為: 2, 4, 8, 16個processes(threading為 threads)的執行時間。
原始的程式的執行方式為: 將**最初的產品頁列表(共30頁html)均分給processes執行**。
base line為Serial的執行時間，執行結果為2421.83秒，實驗結果如下圖所示:
![](https://i.imgur.com/us9Svbr.png)
![](https://i.imgur.com/Xy0Ix6e.png)

ray在2, 4processes的執行結果較優秀，8, 16processes的部分multiprocessing為最佳。
ray能在2, 4processes較為優異而8, 16processes較差的原因我們討論後得出的結論為:
1. ray的架構在執行效能上優於multiprocessing
2. ray有在中間插入server層的機制，worker需要對server做回報，最後主行程再對server取資料，當worker增加時overhead也會隨之增加，也因為爬蟲的應用無法充分發揮ray的效能，因此最終會因為overhead的增加而犧牲掉執行的時間。

threading比較令人訝異的是，隨著threads的增加速度也會有所提升，顛覆我們原先預期的”python支援的threading無法對程式產生加速”的想法。
threading能產生加速的原因主要為:
1. threading支援異步處理(但只是task間快速切換，本身並無加速)
2. requests的等待時間為程式的主要耗時區域，可以藉由threading異步的方式均攤掉。
以下圖為例:
![](https://i.imgur.com/rr8v3uG.png)
在程式執行的時間內，當發起第一個requests時可以交由thread1 處理，也因為threading的機制，程式可以在thread1開始處理requests後馬上處理下一步驟，下一個步驟又能再發起第二個requests並交由thread 2處理，以此類推，能將多個requests的等待時間重疊，最後達到加速的效果。

不過，threading本身在"資料處理"上還是無法平行的，只能以"並行"的方式處理，也因為爬蟲的資料量龐大的關係，各個thread在同一個cpu core執行下，資料擷取與拼裝的時間也會隨之拉長，這也是為什麼threading的方式在越多的threads執行下，效能會與multiprocessing, ray差異越大。
以上的做法還有一個問題，因為產品的評論是”**相當不平均的**”，有的產品可能只有個位數個評論，有的則有上百則評論，而評論的取得是需要發requests去爬取的，當評論數量不平均時各個產品的爬蟲速度也會因為requests的等待時間而有極大的差異。
為了消弭process間處理時間的unbalance問題，我們利用”Pool”的方式來達到Load-balanced。但threading本身的套件並不支援Pool的機制，因此threading的部分我們是以"最大化均攤requests等待時間"的方式來實作，實作的方法為碰到requests就分派thread去處理，總共發起了1945個threads。
threading的做法已是最大化程式效能的方式，所以multiprocessing與ray也都是開最多processes的方式來達到最大化程式效能，因此，比較的結果僅有16processes對比threading的方式。

為了達到Load-balanced需在程式碼上做些改動，所以base line的部分根據改動後的結果再執行了一次，執行結果為2458.83秒，實驗結果如下圖所示:
![](https://i.imgur.com/KqllXlt.png)
![](https://i.imgur.com/ZPAHpJ2.png)

三種方法在Load-balanced後的執行結果在速度上都有再進一步的提升，process的執行效率也隨之上升，但threading的作法是開了1945個threads的關係，所以效率是明顯下降的。
實驗的結果都是以multiprocessing的結果較為優秀。
