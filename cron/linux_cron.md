# broadcast/WokStar.sh 直播                                                                                                                                                                                                           
01 0,5,10,19 * * * /bin/bash /home/work/prod/ytb-stream/broadcast/WokStar.sh 01 2.3 > /home/work/logs/WokStar.log 2>&1
31 2,7,12,21 * * * /bin/bash /home/work/prod/ytb-stream/broadcast/WokStar.sh 02 2.3 > /home/work/logs/WokStar.log 2>&1
 
01 0,5,10,19 * * * /bin/bash /home/work/prod/ytb-stream/broadcast/TasteofChinaStreets.sh 02 2.3 > /home/work/logs/TasteofChinaStreets.log 2>&1
31 2,7,12,21 * * * /bin/bash /home/work/prod/ytb-stream/broadcast/TasteofChinaStreets.sh 01 2.3 > /home/work/logs/TasteofChinaStreets.log 2>&1
 
# 10个视频每天组
# video/WokStar.sh 上传视频
1 8,9,12,13,14,17,20,21,22,23 * * * /bin/bash /home/work/prod/ytb-stream/video/WokStar.sh > /home/work/logs/video/WokStar.sh.log 2>&1
# 修改为兴仔
#1 8,9,12,13,14,17,20,21,22,23 * * * /bin/bash /home/work/prod/ytb-stream/video/EasyTastyRecipes.sh > /home/work/logs/video/EasyTastyRecipes.sh.log 2>&1
 
# 美女视频
1 8,9,12,13,14,17,20,21,22,23 * * * /bin/bash /home/work/prod/ytb-stream/video/SnackFoodHacker.sh > /home/work/logs/video/SnackFoodHacker.sh.log 2>&1
1 8,9,12,13,14,17,20,21,22,23 * * * /bin/bash /home/work/prod/ytb-stream/video/StreetFoodHacker.sh > /home/work/logs/video/StreetFoodHacker.sh.log 2>&1
 
# video/TasteofChinaStreets.sh 每小时上传一个视频 可无限上传
5 8,9,12,13,14,17,20,21,22,23 * * * /bin/bash /home/work/prod/ytb-stream/video/TasteofChinaStreets.sh > /home/work/logs/video/TasteofChinaStreets.sh.log 2>&1
 
 
# 无限个视频每天组
# Gravity Defiers
3 * * * * /bin/bash /home/work/prod/ytb-stream/video/StreetFoodSecrets.sh > /home/work/logs/video/StreetFoodSecrets.sh.log 2>&1
 
# 大杂烩测试
# 2 * * * * /bin/bash /home/work/prod/ytb-stream/video/QuickSnackMasters.sh > /home/work/logs/video/QuickSnackMasters.sh.log 2>&1
