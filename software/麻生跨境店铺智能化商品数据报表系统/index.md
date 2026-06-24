题目：麻生销售数据大屏智能化系统

数据仓库-sql逻辑的模块功能，有以下目录：
- /Users/a1/Documents/Office/code/ms-warehouse-batch-data/day/sales/ads/ads_sales_pid_dashboard_1d.sql
- /Users/a1/Documents/Office/code/ms-warehouse-batch-data/day/sales/ads/ads_sales_store_market_1d.sql
- 
这几个文件，是ads 层的最终查询sql，可以往前追溯

  
java代码的目录
- 整体架构：/Users/a1/Documents/Office/code/ms-bi
- 具体代码目录：/Users/a1/Documents/Office/code/ms-bi/ms-bi/src/main/java/com/ms/bi/tkdashboard/controller/TkPidController.java
- /Users/a1/Documents/Office/code/ms-bi/ms-bi/src/main/java/com/ms/bi/tkdashboard/controller/TkImportController.java
- /Users/a1/Documents/Office/code/ms-bi/ms-bi/src/main/java/com/ms/bi/tkdashboard/controller/TkImportHistoryController.java
- /Users/a1/Documents/Office/code/ms-bi/ms-bi/src/main/java/com/ms/bi/tkdashboard/controller/TkProductStatsController.java
- /Users/a1/Documents/Office/code/ms-bi/ms-bi/src/main/java/com/ms/bi/tkdashboard/controller/TkStoreStatsController.java


前端的代码目录为：
- /Users/a1/Documents/Office/code/web-fms/packages/bi/views/tkboard/pid-board
- /Users/a1/Documents/Office/code/web-fms/packages/bi/views/tkboard/shop-board
- /Users/a1/Documents/Office/code/web-fms/packages/bi/views/tkboard/stock-board

截图的位置为：
- /Users/a1/Documents/Office/code/ms-proj/software/麻生销售数据大屏智能化系统/image

数据仓库是Doris， mysql
调度系统是 海豚调度
