"""Re-create the fictional raw material and high-level plan (no page coordinates)."""
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from compose import prepare,write

root=Path(__file__).resolve().parents[1]
w=root/'examples/visual-defaults'
paragraphs=[
    '# 弧光 / ARC — 产品概念材料',
    '弧光是一款虚构的自适应桌面照明概念。主题：自适应桌面照明。概念提案 / PRODUCT CONCEPT。全部产品、图片与数值均为虚构设计演示，不代表真实产品性能或调研结论。',
    '功能设想：环境感知——采集桌面环境光，作为调光输入。自适应调光——根据当前任务调节光线，不预设所有场景都需要更亮。手动控制——保留用户的调节选择，允许随时接管。',
    '虚构任务调查（单选，100份回答）：阅读45%，屏幕工作30%，手作15%，其他10%。阅读是出现最多的桌面任务。',
    '虚构使用时长结构：总时长100%，家庭书桌50%，共享工作位30%，临时阅读角20%。占比的分母是全部示例使用时长，不是用户人数。',
    '虚构试用进度：1月14人、2月20人、3月28人、4月39人、5月50人、6月64人。试用人数逐月累计；这组样本不代表市场规模或增长预测。',
    '同一虚构操作脚本的动作次数，原方案与概念方案依次为：调亮6次与2次，恢复5次与2次，记忆4次与1次。两组测试条件相同；少做几步不等同于已验证的效率改善。',
    '虚构能耗核算（Wh）：基准100，自适应-12，待机-8，增亮+5，方案85。这是一个假设工况的收支核算，不能作为真实节能测试。',
    '一次调光流程依次为：感知——采集环境光；评估——结合当前任务；调节——改变灯光输出；确认——接受手动接管。这是功能逻辑，不是已经验证的电路设计。',
    '系统结构：弧光照明系统包含感知模块、控制模块、照明模块。感知模块接收环境光输入，控制模块结合自动与手动选择，照明模块输出光线。产品尚未确定售价、上市时间或真实量产参数。'
]
raw='\n\n'.join(paragraphs)+'\n'
(w/'announcement.md').write_text(raw,encoding='utf-8')
if not (w/'source.json').exists():source=prepare(w/'announcement.md',w)
else:
    source=json.loads((w/'source.json').read_text())
    assert (w/source['path']).read_text()==raw,'Use a fresh workspace for changed raw material'
claims={}
def claim(key,value,unit):
    claims[key]={'text':str(value),'evidence':[{'unit':f'p{unit:03}','quote':paragraphs[unit-1]}]}
    return '$'+key
foot=claim('disclosure','全部产品、图片与数值均为虚构设计演示，不代表真实产品性能或调研结论。',2)
def slide(title,unit,reason,**fields):
    i=len(slides);slides.append(dict(title=claim('title'+str(i),title,unit),footnote=foot,design_reason=reason,**fields))
slides=[]
slide('弧光',2,'产品名称与右侧摄影形成一个明确焦点，留白容纳原生标题。',role='cover',
      subtitle=claim('subtitle','自适应桌面照明',2),body=claim('intro','概念提案 / PRODUCT CONCEPT',2),
      illustration={'asset':'hero','subject':'Original fictional adaptive desk lamp with flat graphite circular head, brass hinge and graphite stem/base on a warm ivory desktop.',
                    'purpose':'Establish the product silhouette and a quiet launch mood.','placement':'right','product':True})
items=[]
for i,(a,b) in enumerate([('环境感知','采集桌面环境光，作为调光输入。'),('自适应调光','根据当前任务调节光线，不预设所有场景都需要更亮。'),('手动控制','保留用户的调节选择，允许随时接管。')]):
    items.append({'title':claim('feature'+str(i),a,3),'body':claim('feature-body'+str(i),b,3)})
slide('随环境调光，保留手动选择',3,'一张材质特写配合三段完整功能说明；图标标识具体功能，避免彩色卡片。',relation='capabilities',items=items,
      illustration={'asset':'detail','subject':'Macro photograph of the same fictional lamp head-to-stem brass hinge and matte graphite material.',
                    'purpose':'Show tactile product character beside functional explanations.','placement':'detail','product':True})
def points(prefix,labels,values,unit):
    return [{'label':claim(prefix+'label'+str(i),a,unit),'value':claim(prefix+'value'+str(i),b,unit)} for i,(a,b) in enumerate(zip(labels,values))]
slide('阅读是最多见的桌面任务',4,'类别排名使用排序条形图；重点是阅读，其余类别保持中性。',
      chart={'type':'auto','intent':'ranking','series':[{'name':'任务','points':points('rank',['阅读','屏幕工作','手作','其他'],[45,30,15,10],4)}],
             'focus_points':[0],'focus_reason':'阅读在单选回答中占比最高。','number_format':'0"%"','max':50},
      insight={'value':claim('rank-focus','45%',4),'label':claim('rank-focus-label','阅读任务占比',4),
               'body':claim('rank-note','虚构任务调查：100份单选回答。',4)})
slide('一半使用时长发生在家庭书桌',5,'同一总时长的三个组成部分使用环形图与直接标注，分母紧邻图形。',
      chart={'type':'auto','intent':'share','series':[{'name':'使用时长','points':points('share',['家庭书桌','共享工作位','临时阅读角'],[50,30,20],5)}],
             'whole':claim('whole','示例使用时长',5),'total':claim('total','100',5),'center':claim('center','50%',5),'unit':'%'},
      body=claim('share-note','分母为全部示例使用时长，不是用户人数。',5))
slide('试用人数的逐月累计',6,'按月份保留顺序，以连续折线显示同一指标，避免把时间点排成类别排名。',
      chart={'type':'auto','intent':'trend','series':[{'name':'试用人数','points':points('trend',['1月','2月','3月','4月','5月','6月'],[14,20,28,39,50,64],6)}],
             'number_format':'0','min':0,'max':80,'major_unit':20},
      body=claim('trend-note','虚构试用样本，不代表市场规模或增长预测。',6))
before=points('before',['调亮','恢复','记忆'],[6,5,4],7)
after=[{'label':p['label'],'value':claim('after'+str(i),value,7)} for i,(p,value) in enumerate(zip(before,[2,2,1]))]
slide('同一操作脚本中的动作次数',7,'相同任务的两组值在共享刻度上以哑铃图对照；端点直接写明数值。',
      chart={'type':'auto','intent':'paired','series':[{'name':claim('before-name','原方案',7),'points':before},
             {'name':claim('after-name','概念方案',7),'points':after}],'unit':'次','min':0,'max':8},
      subtitle=claim('paired-note','测试条件相同；动作更少不等同于已验证的效率改善。',7))
slide('假设工况下的能耗核算',8,'可正可负的变化从基准逐步连接至结余，瀑布图在比例和加总上保持一致。',
      chart={'type':'auto','intent':'contribution','series':[{'name':'能耗','points':points('bridge',['基准','自适应','待机','增亮','方案'],[100,-12,-8,5,85],8)}],
             'steps':['total','delta','delta','delta','total'],'unit':'Wh'},
      subtitle=claim('bridge-note','这是假设工况的收支核算，不是真实节能测试。',8))
nodes=[]
for i,(a,b) in enumerate([('感知','采集环境光'),('评估','结合当前任务'),('调节','改变灯光输出'),('确认','接受手动接管')]):
    nodes.append({'id':'stage'+str(i),'title':claim('stage'+str(i),a,9),'body':claim('stage-body'+str(i),b,9)})
slide('一次调光的功能逻辑',9,'顺序关系用连续箭头和一致线性图标表达，文字与图形形成同一条阅读路径。',relation='process',diagram={'nodes':nodes},
      body=claim('process-note','这是功能逻辑，不是已经验证的电路设计。',9))
nodes=[{'id':'root','title':claim('system','弧光照明系统',10),'icon':'illuminate'}]
for i,(a,b,icon) in enumerate([('感知模块','接收环境光输入','sense'),('控制模块','结合自动与手动选择','control'),('照明模块','输出光线','illuminate')]):
    nodes.append({'id':'module'+str(i),'parent':'root','title':claim('module'+str(i),a,10),'body':claim('module-body'+str(i),b,10),'icon':icon})
slide('系统结构',10,'真实父子关系用分支连接表达；不把组成关系画成时间流程。',relation='hierarchy',diagram={'nodes':nodes},
      body=claim('availability','尚未确定售价、上市时间或真实量产参数。',10))
plan={'source_sha256':source['sha256'],'title':'弧光 / ARC — 自动视觉构成样例','language':'zh-CN','slide_count':len(slides),
      'visual_defaults':{'tone':'precise','accent':'B0772A','background':'F4F3EE','ink':'202623',
                         'basis':'Supplied fictional product imagery: graphite metal, brass hinge and ivory light. Typography stays neutral; brass identifies semantic emphasis.'},
      'claims':claims,'slides':slides,'omitted':[],
      'assets':{key:{'path':'assets/'+key+'.jpg','purpose':purpose,'provenance':'Built-in imagegen; full prompt and identity reference recorded in prompts.json. Fictional design illustration.','fit':'cover'}
                for key,purpose in [('hero','Product silhouette with native text-safe area'),('detail','Product material close-up beside functional explanations')]}}
write(w/'plan.json',plan)
print('Wrote fictional source and nine-page semantic plan without layout coordinates or font names.')
