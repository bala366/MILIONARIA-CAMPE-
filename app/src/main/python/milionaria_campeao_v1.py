# -*- coding: utf-8 -*-
"""+MILIONARIA CAMPEAO V1: auditoria das 44 falhas, superposicoes e busca exaustiva.
Executa localmente no Windows. A classificacao nao altera a chance matematica de cada aposta.
"""
import itertools, math, re, sys, time, traceback
from pathlib import Path
from collections import Counter

BLOCKS=[tuple(range(5*i+1,5*i+6)) for i in range(10)]
BID={v:i for i,b in enumerate(BLOCKS) for v in b}
FULL=(1<<50)-1
TOTAL=math.comb(50,6)

def mask(seq):
    m=0
    for v in seq:m|=1<<(v-1)
    return m

def read_history(path):
    data=Path(path).read_bytes()
    text=None
    for enc in ('utf-8-sig','cp1252','latin-1'):
        try:text=data.decode(enc);break
        except UnicodeDecodeError:pass
    rows={}; rejected=[]; duplicates=[]
    for line_no,original in enumerate(text.splitlines(),1):
        line=original.strip()
        if not line:continue
        # Exclui datas, inclusive 11/10/2026 e 2026-10-11.
        clean=re.sub(r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',' ',line)
        clean=re.sub(r'\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\b',' ',clean)
        vals=[int(v) for v in re.findall(r'(?<!\d)\d+(?!\d)',clean)]
        if not vals:
            rejected.append((line_no,line[:120]));continue
        found=None
        # Concurso + 6 dezenas + 2 trevos, com possiveis colunas adicionais.
        if len(vals)>=9 and vals[0]>=1:
            for start in range(1,len(vals)-7):
                balls=vals[start:start+6]; trevos=vals[start+6:start+8]
                if len(set(balls))==6 and all(1<=x<=50 for x in balls) and len(set(trevos))==2 and all(1<=x<=6 for x in trevos):
                    found=(vals[0],tuple(sorted(balls)),tuple(sorted(trevos)));break
        elif len(vals)==8:
            balls=vals[:6];trevos=vals[6:]
            if len(set(balls))==6 and all(1<=x<=50 for x in balls) and len(set(trevos))==2 and all(1<=x<=6 for x in trevos):
                found=(line_no,tuple(sorted(balls)),tuple(sorted(trevos)))
        if found:
            contest,balls,trevos=found
            if contest in rows and rows[contest]!=(balls,trevos):duplicates.append((contest,line_no))
            rows[contest]=(balls,trevos)
        else:rejected.append((line_no,line[:120]))
    return sorted(rows.items()),rejected,duplicates

def streak(flags):
    count=0
    for v in reversed(flags):
        if not v:break
        count+=1
    return count

def analysis(history,output,rejected,duplicates):
    n=len(history)
    draws=[balls for _,(balls,_) in history]
    trevos=[ts for _,(_,ts) in history]
    dm=[mask(x) for x in draws]
    tm=[mask(x) for x in trevos]
    print('ETAPA 1/4 - 44 FALHAS E SUPERPOSICAO DE TODOS OS CONCURSOS',flush=True)
    # Intersecao entre listas de 44 ausentes e igual a 38 + intersecao dos sorteados.
    overlaps=Counter();closest=[]
    for i,mi in enumerate(dm):
        best=(-1,-1)
        for j in range(i):
            shared=(mi&dm[j]).bit_count()
            overlaps[38+shared]+=1
            if shared>best[0]:best=(shared,j)
        if best[1]>=0:closest.append((best[0],i,best[1]))
        if (i+1)%300==0:print(f'  {i+1}/{n} concursos comparados',flush=True)
    print('ETAPA 2/4 - CRESCIMENTO DAS FALHAS, BLOCOS, PADROES E TREVOS',flush=True)
    w=min(50,max(1,n//2))
    number=[]
    for x in range(1,51):
        miss=[not (m>>(x-1)&1) for m in dm]
        number.append(dict(n=x,ausencias=sum(miss),sequencia=streak(miss),recente=sum(miss[-w:])/w,anterior=sum(miss[-2*w:-w])/w))
    block=[]
    for i,b in enumerate(BLOCKS,1):
        bm=mask(b);flags=[(m&bm)==0 for m in dm]
        block.append(dict(bloco=i,dez=b,sem_dezenas=sum(flags),sequencia=streak(flags),recente=sum(flags[-w:])/w,anterior=sum(flags[-2*w:-w])/w))
    blockpairs=[]
    for i,j in itertools.combinations(range(10),2):
        bm=mask(BLOCKS[i]+BLOCKS[j]);flags=[(m&bm)==0 for m in dm]
        blockpairs.append((i+1,j+1,sum(flags),streak(flags)))
    rep=Counter(len(set(draws[i])&set(draws[i-1])) for i in range(1,n))
    tr_rep=Counter(len(set(trevos[i])&set(trevos[i-1])) for i in range(1,n))
    blockshape=Counter(tuple(sorted(Counter(BID[x] for x in balls).values(),reverse=True)) for balls in draws)
    odd=Counter(sum(x%2 for x in balls) for balls in draws)
    sums=Counter(sum(balls)//20 for balls in draws)
    span=Counter((balls[-1]-balls[0])//10 for balls in draws)
    gaps=Counter(tuple(b-a for a,b in zip(balls,balls[1:])) for balls in draws)
    bmask_hist=Counter(sum(1<<BID[x] for x in balls) for balls in draws) # soma nao serve como mascara, abaixo corrige
    bmask_hist=Counter(sum(1<<i for i in {BID[x] for x in balls}) for balls in draws)
    trevo_pairs=Counter(trevos)
    trevo_miss=[]
    for t in range(1,7):
        f=[t not in pair for pair in trevos]
        trevo_miss.append((t,sum(f),streak(f),sum(f[-w:])/w,sum(f[-2*w:-w])/w))
    # Relatorio escrito antes de qualquer enumeracao de apostas.
    report=output/'AUDITORIA_ANTES_DO_JOGO_V1.txt'
    with report.open('w',encoding='utf-8') as f:
        def p(*v):print(*v,file=f)
        p('+MILIONARIA CAMPEAO V1 - AUDITORIA COMPLETA ANTES DO JOGO')
        p('Historico:',n,'concursos. Primeiro:',history[0][0],'Ultimo:',history[-1][0]);p('Rejeitadas:',len(rejected),'Duplicadas divergentes:',duplicates)
        p('Concursos faltantes:',sorted(set(range(history[0][0],history[-1][0]+1))-set(c for c,_ in history))[:200])
        p('Ultimo resultado:',draws[-1],'Trevos:',trevos[-1])
        p('\nSUPERPOSICAO DAS 44 FALHAS:')
        p('Em 50 dezenas com 6 sorteadas, duas listas de 44 ausentes compartilham no minimo 38/44 = 86,36%.')
        p('70% e 80% nao distinguem os resultados. 90% requer 40 ou mais ausencias em comum.')
        p('Pares comparados:',n*(n-1)//2,'Distribuicao de coincidencias:',sorted(overlaps.items()))
        p('Pares de concursos mais parecidos:')
        for shared,i,j in sorted(closest,reverse=True)[:30]:p(history[j][0],history[i][0],38+shared,'/44',round((38+shared)/44*100,2),'%')
        p('\n44 FALHAS CONCURSO A CONCURSO + 4 TREVOS AUSENTES:')
        for (contest,(balls,ts)),m,t in zip(history,dm,tm):
            p('CONCURSO',contest,'DEZENAS',balls,'TREVOS',ts,'FALHAS',tuple(x for x in range(1,51) if not (m>>(x-1)&1)),'TREVOS AUSENTES',tuple(x for x in range(1,7) if not (t>>(x-1)&1)))
        p('\nFALHAS POR DEZENA: (ausencias, sequencia, ultimos 50, janela anterior)')
        for row in number:p(row)
        p('\nBLOCOS SEM NENHUMA DEZENA SORTEADA:')
        for row in block:p(row)
        p('\n45 DUPLAS DE BLOCOS AUSENTES:')
        for row in blockpairs:p(row)
        p('\nREPETIDAS DO CONCURSO ANTERIOR:',sorted(rep.items()))
        p('REPETIDAS DOS TREVOS:',sorted(tr_rep.items()))
        p('DISTRIBUICAO POR BLOCOS:',blockshape.most_common())
        p('MASCARAS DE BLOCOS OCUPADOS:',bmask_hist.most_common(20))
        p('IMPARES:',odd.most_common(),'SOMA FAIXA 20:',sums.most_common(),'AMPLITUDE:',span.most_common())
        p('INTERVALOS ENTRE DEZENAS:',gaps.most_common(30))
        p('TREVOS PARES:',trevo_pairs.most_common())
        p('FALHAS INDIVIDUAIS DE TREVOS:',trevo_miss)
        p('\nIMPORTACAO - LINHAS REJEITADAS:')
        for row in rejected:p(row)
    return locals()

def select_game(stats):
    print('ETAPA 3/4 - 15.890.700 COMBINACOES DE 6 DEZENAS',flush=True)
    history=stats['history']; draws=stats['draws'];last=set(draws[-1]);n=len(history)
    number=stats['number'];blockshape=stats['blockshape'];odd=stats['odd'];sums=stats['sums'];span=stats['span'];bmask_hist=stats['bmask_hist'];rep=stats['rep']
    # Preferencia por exatamente uma repetida, como no motor Mega V9.
    # Toda combinacao ainda e enumerada e contabilizada; filtro e declarado.
    weights=[0]*51
    for r in number:
        growth=r['recente']-r['anterior']
        weights[r['n']]=int(240*(1-r['recente'])-130*growth-min(r['sequencia'],45)*1.8)
    # Frequencia de pares historicos da suporte a coocorrencia, nao previsao.
    pair_freq=[[0]*51 for _ in range(51)]
    for balls in draws:
        for a,b in itertools.combinations(balls,2):pair_freq[a][b]+=1
    pair_bonus=[[int(8*math.log1p(pair_freq[a][b])) for b in range(51)] for a in range(51)]
    def build_scores(counts,coef):return {key:int(coef*math.log1p(freq)) for key,freq in counts.items()}
    sh_score=build_scores(blockshape,55);odd_score=build_scores(odd,38);sum_score=build_scores(sums,35);span_score=build_scores(span,35);mask_score=build_scores(bmask_hist,35)
    best=(-10**15,None,None); processed=0;eligible=0;t0=time.monotonic()
    for combo in itertools.combinations(range(1,51),6):
        processed+=1
        if sum(x in last for x in combo)==1:
            eligible+=1
            a,b,c,d,e,f=combo
            score=weights[a]+weights[b]+weights[c]+weights[d]+weights[e]+weights[f]
            score+=pair_bonus[a][b]+pair_bonus[a][c]+pair_bonus[a][d]+pair_bonus[a][e]+pair_bonus[a][f]
            score+=pair_bonus[b][c]+pair_bonus[b][d]+pair_bonus[b][e]+pair_bonus[b][f]
            score+=pair_bonus[c][d]+pair_bonus[c][e]+pair_bonus[c][f]+pair_bonus[d][e]+pair_bonus[d][f]+pair_bonus[e][f]
            counts=Counter(BID[x] for x in combo)
            shape=tuple(sorted(counts.values(),reverse=True))
            occupied=sum(1<<i for i in counts)
            sm=sum(combo)
            score+=sh_score.get(shape,0)+mask_score.get(occupied,0)+odd_score.get(sum(x%2 for x in combo),0)+sum_score.get(sm//20,0)+span_score.get((f-a)//10,0)
            if score>best[0]:best=(score,combo,dict(blocos=tuple(sorted(i+1 for i in counts)),distribuicao=shape,repetida=tuple(x for x in combo if x in last),soma=sm,intervalos=tuple(y-x for x,y in zip(combo,combo[1:]))))
        if processed%250000==0:
            print(f'  {processed:,}/{TOTAL:,} | {processed/TOTAL:.1%} | elegiveis {eligible:,} | {time.monotonic()-t0:.1f}s | melhor {best[1]}',flush=True)
    return best,processed,eligible

def select_trevos(stats):
    print('ETAPA 4/4 - 15 PARES DE TREVOS E PDF',flush=True)
    trevos=stats['trevos'];n=len(trevos);w=stats['w'];freq=Counter(trevos)
    singles=Counter(x for pair in trevos for x in pair)
    scores=[]
    for pair in itertools.combinations(range(1,7),2):
        recent=sum(x in p for p in trevos[-w:] for x in pair)
        prev=sum(x in p for p in trevos[-2*w:-w] for x in pair)
        run=sum(1 for p in reversed(trevos) if pair[0] not in p and pair[1] not in p)
        score=20*freq[pair]+5*(singles[pair[0]]+singles[pair[1]])-5*(recent-prev)+min(run,15)
        scores.append((score,pair))
    scores.sort(reverse=True)
    return scores[0],scores

def pdf(path,stats,best,trevo_best):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    c=canvas.Canvas(str(path),pagesize=A4);W,H=A4
    blue=HexColor('#1779B9');dark=HexColor('#17486C');green=HexColor('#128449')
    c.setFillColor(blue);c.roundRect(38,H-105,W-76,65,10,fill=1,stroke=0)
    c.setFillColor(HexColor('#FFFFFF'));c.setFont('Helvetica-Bold',22);c.drawCentredString(W/2,H-78,'+MILIONARIA CAMPEAO')
    c.setFillColor(dark);c.setFont('Helvetica-Bold',12);c.drawCentredString(W/2,H-132,'VOLANTE DIVIDIDO EM 10 BLOCOS')
    c.setFont('Helvetica',9);c.drawCentredString(W/2,H-149,'10 blocos de 5 dezenas | 6 dezenas marcadas em verde')
    chosen=set(best[1]);x0=38;bw=(W-76)/5;top=H-173;bh=195;gap=20
    for i,block in enumerate(BLOCKS):
        col=i%5;band=i//5;x=x0+col*bw;y=top-band*(bh+gap)
        c.setFillColor(HexColor('#F8FBFD'));c.setStrokeColor(blue);c.setLineWidth(1.4)
        c.rect(x,y-bh,bw,bh,fill=1,stroke=1)
        c.setFillColor(blue);c.rect(x,y-29,bw,29,fill=1,stroke=0)
        c.setFillColor(HexColor('#FFFFFF'));c.setFont('Helvetica-Bold',10);c.drawCentredString(x+bw/2,y-19,'BLOCO '+str(i+1))
        for j,num in enumerate(block):
            cx=x+bw/2;cy=y-48-j*27
            c.setStrokeColor(HexColor('#CEDCE5'));c.setLineWidth(.7);c.circle(cx,cy,12,stroke=1,fill=0)
            if num in chosen:
                c.setFillColor(HexColor('#E3F5E8'));c.circle(cx,cy,12,stroke=0,fill=1)
                c.setStrokeColor(green);c.setLineWidth(2.5);c.circle(cx,cy,12,stroke=1,fill=0)
            c.setFillColor(green if num in chosen else dark);c.setFont('Helvetica-Bold',11);c.drawCentredString(cx,cy-4,'%02d'%num)
    y=top-2*bh-gap-30
    c.setFillColor(dark);c.setFont('Helvetica-Bold',12);c.drawCentredString(W/2,y,'TREVOS - MARCADOS EM VERDE')
    ts=set(trevo_best[1])
    for t in range(1,7):
        cx=W/2+(t-3.5)*67;cy=y-36
        c.setStrokeColor(blue);c.setLineWidth(1);c.circle(cx,cy,18,fill=0,stroke=1)
        if t in ts:
            c.setFillColor(HexColor('#E3F5E8'));c.circle(cx,cy,18,stroke=0,fill=1)
            c.setStrokeColor(green);c.setLineWidth(3);c.circle(cx,cy,18,fill=0,stroke=1)
        c.setFillColor(green if t in ts else dark);c.setFont('Helvetica-Bold',14);c.drawCentredString(cx,cy-5,str(t))
    c.setFillColor(dark);c.setFont('Helvetica-Bold',11)
    c.drawCentredString(W/2,y-80,'DEZENAS: '+' - '.join('%02d'%x for x in best[1]))
    c.drawCentredString(W/2,y-98,'TREVOS: '+' e '.join(map(str,trevo_best[1])))
    c.setFont('Helvetica',8);c.drawCentredString(W/2,40,'Modelo estatistico retrospectivo; nao aumenta a probabilidade matematica de acerto.')
    c.drawCentredString(W/2,27,'Volante de estudo, nao oficial. Consulte a auditoria completa antes de apostar.')
    c.save()

def main():
    from tkinter import Tk,filedialog
    print('=== +MILIONARIA CAMPEAO V1 | FALHAS PRIMEIRO, JOGO DEPOIS ===',flush=True)
    root=Tk();root.withdraw();root.attributes('-topmost',True)
    path=filedialog.askopenfilename(title='Selecione o TXT/CSV da +Milionaria',filetypes=[('Historico','*.txt *.csv'),('Todos','*.*')]);root.destroy()
    if not path:print('Selecao cancelada.');return
    history,rejected,duplicates=read_history(path)
    print('Concursos validos:',len(history),'| linhas rejeitadas:',len(rejected),'| duplicatas divergentes:',len(duplicates),flush=True)
    if len(history)<10:
        print('ERRO: menos de 10 concursos. Formato esperado: 1 - 01 08 14 22 31 45 - 2 5')
        print('Exemplos de linhas rejeitadas:',rejected[:6]);return
    output=Path.home()/'Desktop'/'RESULTADOS_MILIONARIA_CAMPEAO_V1'
    if not output.parent.exists():output=Path(path).parent/'RESULTADOS_MILIONARIA_CAMPEAO_V1'
    output.mkdir(parents=True,exist_ok=True)
    print('Resultados em:',output,flush=True)
    stats=analysis(history,output,rejected,duplicates)
    print('Auditoria salva:',stats['report'],flush=True)
    best,processed,eligible=select_game(stats)
    trevo_best,trevo_scores=select_trevos(stats)
    with (output/'RELATORIO_JOGO_V1.txt').open('w',encoding='utf-8') as f:
        f.write('+MILIONARIA CAMPEAO V1\n')
        f.write('Concursos: %d\nComb. enumeradas: %d\nElegiveis com exatamente uma repetida: %d\n'%(len(history),processed,eligible))
        f.write('Jogo: %s\nPontuacao: %s\nPadroes: %s\n'%(best[1],best[0],best[2]))
        f.write('Trevos: %s\nRanking dos 15 pares: %s\n'%(trevo_best[1],trevo_scores))
        f.write('Classificacao historica; nao prediz sorteios futuros.\n')
    pdf_path=output/'VOLANTE_MILIONARIA_CAMPEAO_V1.pdf'
    pdf(pdf_path,stats,best,trevo_best)
    print('CONCLUIDO! JOGO:',best[1],'TREVOS:',trevo_best[1]);print('PDF:',pdf_path,flush=True)

if __name__=='__main__':
    try:main()
    except Exception:
        traceback.print_exc();input('ERRO. Pressione ENTER para sair...');sys.exit(1)
