#coding=utf-8
import logging
import json
import time
import random
import search
import re
import sqlite3
import os
import imp
import jieba
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool 

imp.reload(search)



conn = sqlite3.connect("qq_bot_database.db")
cu = conn.cursor()
cu.execute("DELETE FROM learn_data WHERE content LIKE '%找不到这个知识呀%'")
conn.commit()

def reset_database():
    cu.execute("SELECT * FROM learn_data")
    result = cu.fetchall()
    tmp = []
    for i in result:
        tmp.append(i[2:])

    tmp = list(set(tmp))

    cu.execute("DELETE FROM learn_data")
    conn.commit()
    for line in tmp:
        cu.execute('INSERT INTO learn_data(name,content) VALUES(?,?)',line)
    conn.commit()

reset_database()



rep_comment = ['ヽ(｀Д´)ﾉ','_(:з」∠)_','Σ(oﾟдﾟoﾉ)',' щ(ﾟДﾟщ)','(╬￣皿￣)=○',' (*´ﾉ皿`)','(￣^￣)ゞ','!!!∑(°Д°ノ)ノ','(▼皿▼#)','٩(˃̶͈̀௰˂̶͈́)و','╮（╯＿╰）╭','你才智障呢！口亨~'] 

try:
    cu.execute("create table learn_data (id integer primary key,pid integer UNIQUE ,name varchar(140) ,content text NULL)")
except:
    print 'table exists..'

sleeptime = 0.1
logging.basicConfig(filename='log.log', level=logging.DEBUG, format='%(asctime)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
last1 = ''
administrator = []
root = []
bot_document = '管理员专用指令：\n./selfcheck(自检）\n./learn '+'{'+'关键词}'+'{内'+'容}\n./check（查看已经学会多少知识）\n./add_tip xxx（向tip中添加内容）\n'



def main(send_uin, content, root_name, admini):
    global administrator
    global root
    administrator = admini
    root = root_name



    pattern = re.compile(r'^(?:./|./)(learn|delete) {(.+)}{(.+)}')
    match = pattern.match(content)
    if match:
        try:
            if match.group(1) == 'learn':
                if send_uin in administrator:
                    result = learn(str(match.group(2)).decode('UTF-8'), str(match.group(3)).decode('UTF-8'))    
                else:
                    result = random.choice(['人家才不学这些坏坏的知识呢！','宝宝只学主人和她的小伙伴教的知识！'])
            
            elif match.group(1) == 'delete':
                if send_uin in root:
                    result = delete(str(match.group(2)).decode('UTF-8'), str(match.group(3)).decode('UTF-8'))   
                else:
                    result = '只有主人能叫宝宝忘掉！╭(╯^╰)╮口亨'
        except Exception,e:
            logging.critical(str(e))
        
    else:
        try:
            result = command(send_uin, content)
        except Exception,e:
            logging.critical(str(e))
    
    return result


def command(send_uin, content):

    if './add_tip' in content:
        result = add_tip(send_uin,content)
                

    elif content[:9] == './weather':
        try:
            content = (content.split())[1]
            result = search.get_weather(content)
            result = '接下来七天，'+content+'的天气是：\n'+result
        except Exception,e:
            result = '获取天气信息失败……'
            print e
            logging.info(str(e))

    elif content == './智障机器人':
        result = random.choice(rep_comment)


    elif './tips' in content:
        try:
            joke_index = content.split()[1]
            logging.info('开始讲笑话了')
            try:
                joke_index = int(joke_index)
                cu.execute("select * from tips_data")
                result = cu.fetchall()
                result = result[int(joke_index)][-1]
            except Exception,e:
                logging.critical(str(e))
                cu.execute("select * from tips_data where content like '%"+str(joke_index)+"%'")
                result = cu.fetchall()
                result = (random.choice(result))[-1]
        except:
            cu.execute("select * from tips_data")
            result = cu.fetchall()
            result = (random.choice(result))[-1]     
        logging.info("AI REPLY:"+str(result))


    elif './search' in content:
        result = search_nlg(content)
        

    elif content == './about':
        try:
            logging.info("output about info")
            result = "人家呢~是一个采用麻省理工大学X11协议（MIT协议）的开源学习助手，开发语言是python，作者是菁菁同学（421248329）\n~快向宝宝下命令吧~~使用./explain进行名词解释，允许管理员账号使用./learn功能提交词条，使用./search功能搜索对应的百科词条并保存，如果您学习累了，可以选择./tips命令，宝宝会给您讲笑话哦~"
        except Exception, e:
            logging.error("ERROR"+str(e))


    elif content == './list':
        result ='指令列表:\n./list\n./check\n./learn\n./delete\n./deleteall\n./tips\n./search\n./about\n./shutdown'

    elif content == './document':
        result = bot_document


    elif content == './checklist':
        if send_uin in root:
            cu.execute("select * from learn_data")
            all_know = cu.fetchall()
            kng = []
            for i in all_know:
                kng.append(i[2])
            kng=list(set(kng))            
            result = '宝宝现在的知识库是：'+','.join(kng)
        else:
            result = '权限不足呢~宝宝不告诉你'

    elif content.split()[0] == './cut':
        sentence = ''.join(content.split()[1:])
        seg_list = jieba.cut(sentence)  # 默认是精确模式
        result =  ", ".join(seg_list)
        

 
    elif content == './deleteall':
        if send_uin in root:
            try:
                logging.info("Delete all learned data for group")
                cu.execute("delete from learn_data")
                result = "宝宝经过努力，忘掉这些知识了呢！"
            except Exception, e:
                logging.error("ERROR:"+str(e))
        else:
            result = '宝宝才不会删除这些信息呢！只有主人可以~'

    elif content[:6] == './dict':
        try:
            content = content.split()[1]
            result = search.translate(content)
        except:
            result = '哎呀呀找不到这个词的意思诶'
     

    elif content == './check':
        if send_uin in administrator:
            cu.execute("select * from learn_data")
            count = len(cu.fetchall())

            result = '报告，宝宝学会了'+str(count)+'条知识，快夸我~'
        else:
            result ='只有主人和主人的小伙伴可以看宝宝学了多少知识呢~'

    elif './ask' in content:
        fh = open('name.txt')
        result_list = fh.readlines()
        result = random.choice(result_list)
        fh.close()


    elif content == './greeting':
        if send_uin in root:
            result = random.choice(['主人~您的宝宝回来惹~','主人~宝宝想你惹','宝宝会为主人尽心尽力服务哦~'])
        else:
            result = random.choice(['死变态你是谁啦，人家不认识你啦！','变态！人家还是宝宝呢！','主人说了，宝宝不能和陌生人说话！'])
        
    elif content == './cleanlog':
        if send_uin in root:
            fh = open('log.log','w')
            print '日志清理结束呀~'
            fh.close()
            result = '日志清理结束呀~'
        else:
            result = '权限不足呢，只有主人才能叫宝宝清理日志~'

    elif './roll' in content:
        result = roll(content) 


    elif './executesql' in content:
        if send_uin in root:
            content = content[13:]
            try:
                cu.execute(content)
                if ((content.split())[0]).lower() == 'select':
                    count = len(cu.fetchall())
                    result = '查询到'+str(count)+'条'

                else:
                    conn.commit()
                    result = '操作成功'

            except Exception,e:
                print e
                logging.critical(str(e))
                result = '操作失败'
                print result

        else:
            result = '权限不足呢，只有主人才能操作SQL数据库~'

    elif './roll' in content:
        result = roll(content)

    elif content == './license':
        fh = open('LICENSE','r')
        text = (fh.readlines())[0]
        fh.close()
        result = text

    elif content == './reset_db':
        if send_uin in root:
            reset_database()
            result = '重置数据库成功'
        else:
            result = '权限不足诶~'


    elif './explain' in content:
        try:
            content = content.split()[1]
            cu.execute("select * from learn_data where name ='"+content+"'")
            tmp = cu.fetchall()
            answer = str((random.choice(tmp))[-1])
            result = answer
        except Exception,e:
            print e 
            result = '数据库中没有找到对应内容'


    else:
        content = content[2:]

        search_kw = content
        print content
        content = jieba.cut(content)
        print type(content)
        #先对问题进行分词处理
        content = (','.join(content)).split(',')
        roll_point = random.randint(1,100)
        print roll_point
        try:
            all_answer = []
            for i in content:
                cu.execute("select * from learn_data where name ='"+i+"'")
                tmp = cu.fetchall()
                for j in tmp:
                    all_answer.append(j)

            cu.execute("select * from learn_data where name ='"+search_kw+"'")
            tmp = cu.fetchall()
            if len(tmp) == 0:
                answer = str((random.choice(all_answer))[-1])
                result = answer
            else:
                if roll_point > 80:
                    answer = str((random.choice(all_answer))[-1])
                    result = answer
                else:
                    answer = str((random.choice(tmp))[-1])
                    result = answer
            
            
        except Exception, e:
            print str(e)
            answer = '宝宝的知识库里没有这条知识呀'
            logging.error("ERROR:"+str(e))
            pass


        if answer == '宝宝的知识库里没有这条知识呀':
            content = content+[search_kw]+search_kw.split(u'，')
            search_item = []
            for i in content:
                search_item.append('./search '+i)
            pool = Pool()
            try:
                answer = pool.map(search_nlg,search_item)
                answer = random.choice(answer)

            except:
                pass
            pool.close()
            result = str(answer)
    
    return result


def search_nlg(content):
    logging.info('SEARCH:'+content+'\n')
    url = 'http://baike.baidu.com/item/'+content.split()[1]
    key = content.split()[1]
    try:
        answer = (search.search_info(url)).strip()
        try:
            result = answer[:150]+'...'
        except:
            result = answer
        try:
            value = answer[:150]
        except:
            value = answer
        learn(key,value)
    except Exception, e:
        logging.critical('ERROR'+str(e))
        result = '宝宝找不到这个知识呀~'
    return result

def delete(key, value, needreply=True):
    try:
        cu.execute("delete from learn_data where name = '"+str(key)+"' and content = '"+str(value)+"'")  
        conn.commit() 
        if needreply:
            result = "人家忘掉 " + str(value) + " 了"
    except:
            result = "咦~人家不知道你在说什么啦~"

    return result

def learn(key, value, needreply=True):
    try:
        cu.execute("select * from learn_data where name = '"+str(key)+"'")
        result = cu.fetchall()
        result_index = []
        for i in result:
            result_index.append(i[3:])
            print i[3:]  
            print i  #切割关键词    
        result_index = list(set(result_index))#去重

        t_list = []
        t = key.split(',')+[key] #把关检测根据逗号切割
        for i in t:
            t_list.append((i.decode('utf-8'),value.decode('utf-8')))
        
        t_list = list(set(t_list))

        for t in t_list:
            print t
        if value not in result_index:
            for t in t_list:
                print t
                cu.execute("insert into learn_data(name,content)  values(?,?)", t)
        conn.commit()
        result = ("宝宝学会“" + str(key) + "”了~") 
    except Exception,e:
        print e
        logging.critical('ERROR'+str(e))

    
    return result
 
                                 
def get_cpu_t():
    res =os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=","").replace("'C\n","")) 

def add_tip(send_uin,content):
    global joke_list
    if './add_tip' in content:
        if send_uin in administrator:
            cu.execute("insert into tips_data (content) values(?)",((content.split()[1]),))
            result = '该tip成功写入数据库'
            conn.commit()
        else:
            result = '权限不足，无法写入'
        logging.info(result)
    return result

def roll(content):
    try:
        diceface = int((content.split()[1])[1:])
    except:
        diceface = 20

    if diceface is 0:
        result = '你拿出一颗祖传的克莱因瓶骰子，结果它直接消失在了空气中。'
    elif diceface < 0:
        result = '你尝试丢%d个面的骰子的行为被未来局时空管理处制止了。' % int(diceface)
    elif diceface is 1:
        result = '你发现自己正盯着一个写着阿拉伯数字 1 的莫比乌斯环发呆。'
    elif diceface is 2:
        diceresult = random.randint(0,1)
        result = '你向空中抛出一枚硬币，结果是：%s' % ( u'正面(1)' if diceresult else u'反面(2)' )
    elif diceface <= 1024:
        diceresult = random.randint(1, diceface)
        result = '你丢了一个%d面骰，结果为：%d' % (diceface, diceresult )
        if diceresult <= diceface / 20 or diceresult == 1:
            result += "  …看来您的人品需要充值了呢。"
    else:
        result = '你丢出一个圆滚滚的%d面骰，等到天荒地老这货都没能停下来。' % diceface

    return result


