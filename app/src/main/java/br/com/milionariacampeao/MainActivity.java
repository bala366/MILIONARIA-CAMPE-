package br.com.milionariacampeao;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.content.Intent;
import android.net.Uri;
import android.graphics.*;
import android.graphics.pdf.PdfDocument;
import android.view.*;
import android.widget.*;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import java.io.*;
import java.util.*;

public class MainActivity extends Activity {
    private static final int PICK=1, SAVE=2;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private TextView status;
    private Button start, export;
    private File input, resultDir, pdfFile;
    private int[] chosen, trevos;
    private int contests, lastContest, examined, score;
    private boolean running=false;
    private static final int[][] BLOCKS={
        {1,2,3,4,5},{6,7,8,9,10},{11,12,13,14,15},{16,17,18,19,20},{21,22,23,24,25},
        {26,27,28,29,30},{31,32,33,34,35},{36,37,38,39,40},{41,42,43,44,45},{46,47,48,49,50}};
    @Override public void onCreate(Bundle b){super.onCreate(b);
        if(!Python.isStarted()) Python.start(new AndroidPlatform(this));
        resultDir=new File(getFilesDir(),"RESULTADOS_MILIONARIA_CAMPEAO_V1");resultDir.mkdirs();
        LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(24,30,24,20);
        root.setBackgroundColor(Color.rgb(250,248,243));
        TextView title=new TextView(this);title.setText("+MILIONARIA CAMPEAO V1");title.setTextSize(23);title.setTextColor(Color.rgb(35,116,75));root.addView(title);
        TextView sub=new TextView(this);sub.setText("Motor Windows V1 • 44 falhas • 10 blocos • 15.890.700 jogos • 15 pares de trevos");sub.setTextSize(13);root.addView(sub);
        start=new Button(this);start.setText("1. SELECIONAR HISTORICO TXT/CSV");root.addView(start);
        Button run=new Button(this);run.setText("2. ANALISAR TODOS OS CONCURSOS");root.addView(run);
        export=new Button(this);export.setText("3. SALVAR VOLANTE PDF");export.setEnabled(false);root.addView(export);
        ScrollView scroll=new ScrollView(this);status=new TextView(this);status.setTextSize(14);status.setTextIsSelectable(true);status.setText("Selecione o arquivo do historico para comecar.");scroll.addView(status);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        setContentView(root);
        start.setOnClickListener(v->{Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.setType("*/*");i.addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(i,PICK);});
        run.setOnClickListener(v->begin());
        export.setOnClickListener(v->{Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.setType("application/pdf");i.addCategory(Intent.CATEGORY_OPENABLE);i.putExtra(Intent.EXTRA_TITLE,"VOLANTE_MILIONARIA_CAMPEAO_V1.pdf");startActivityForResult(i,SAVE);});
        handler.postDelayed(new Runnable(){public void run(){if(running){File log=new File(resultDir,"ANDAMENTO.txt");if(log.exists())try{byte[] data=read(log);String s=new String(data,"UTF-8");status.setText(s.length()>5500?s.substring(s.length()-5500):s);}catch(Exception ignored){}}handler.postDelayed(this,1500);}},1500);
    }
    @Override protected void onActivityResult(int req,int res,Intent data){super.onActivityResult(req,res,data);if(res!=RESULT_OK||data==null)return;
        if(req==PICK){try(InputStream in=getContentResolver().openInputStream(data.getData())){
            input=new File(getCacheDir(),"historico_milionaria.txt");try(FileOutputStream out=new FileOutputStream(input)){byte[] buf=new byte[8192];int n;while((n=in.read(buf))!=-1)out.write(buf,0,n);}
            status.setText("Arquivo carregado: "+data.getData()+"\nPronto para analisar.");
        }catch(Exception e){status.setText("Erro ao abrir historico: "+e);}}
        if(req==SAVE&&pdfFile!=null){try(OutputStream out=getContentResolver().openOutputStream(data.getData());FileInputStream in=new FileInputStream(pdfFile)){
            byte[] buf=new byte[8192];int n;while((n=in.read(buf))!=-1)out.write(buf,0,n);status.setText("PDF salvo com sucesso.\n"+data.getData());
        }catch(Exception e){status.setText("Erro ao salvar PDF: "+e);}}
    }
    private void begin(){if(running)return;if(input==null){status.setText("Primeiro selecione o historico.");return;}
        running=true;export.setEnabled(false);status.setText("Iniciando analise completa...\nPode demorar muito no celular. Mantenha o app aberto.");
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        new Thread(()->{try{
            String value=Python.getInstance().getModule("android_bridge").callAttr("run",input.getAbsolutePath(),resultDir.getAbsolutePath()).toString();
            String[] parts=value.split("\\|");String[] nums=parts[0].split(",");chosen=new int[6];for(int i=0;i<6;i++)chosen[i]=Integer.parseInt(nums[i]);
            String[] t=parts[1].split(",");trevos=new int[]{Integer.parseInt(t[0]),Integer.parseInt(t[1])};
            contests=Integer.parseInt(parts[2]);lastContest=Integer.parseInt(parts[3]);examined=Integer.parseInt(parts[4]);score=Integer.parseInt(parts[5]);
            pdfFile=new File(resultDir,"VOLANTE_MILIONARIA_CAMPEAO_V1.pdf");createPdf(pdfFile);
            handler.post(()->{running=false;getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);export.setEnabled(true);status.setText("CONCLUIDO!\nJogo: "+Arrays.toString(chosen)+"\nTrevos: "+Arrays.toString(trevos)+"\nConcursos: "+contests+"\nJogos examinados: "+examined+"\nToque SALVAR VOLANTE PDF.");});
        }catch(Exception e){handler.post(()->{running=false;getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);status.setText("ERRO: "+e+"\nConfira seu TXT e tente novamente.");});}}).start();
    }
    private byte[] read(File f)throws IOException{try(FileInputStream in=new FileInputStream(f);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toByteArray();}}
    private void createPdf(File file)throws IOException{
        PdfDocument pdf=new PdfDocument();
        PdfDocument.PageInfo pi=new PdfDocument.PageInfo.Builder(595,842,1).create();
        PdfDocument.Page page=pdf.startPage(pi);
        Canvas c=page.getCanvas();Paint p=new Paint(3);c.drawColor(Color.WHITE);
        int blue=Color.rgb(27,109,185),green=Color.rgb(18,136,75),dark=Color.rgb(29,68,99);
        p.setColor(blue);c.drawRoundRect(35,38,560,104,10,10,p);
        p.setColor(Color.WHITE);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(24);center(c,p,"+MILIONARIA CAMPEAO",297,80);
        p.setColor(dark);p.setTextSize(13);center(c,p,"VOLANTE DIVIDIDO EM 10 BLOCOS",297,131);
        p.setTypeface(Typeface.DEFAULT);p.setTextSize(10);center(c,p,"10 blocos de 5 dezenas | 6 dezenas marcadas em verde",297,150);
        float left=35,bw=105,top=173,head=28,rowH=27,gh=head+5*rowH,gap=18;
        HashSet<Integer> marked=new HashSet<>();for(int x:chosen)marked.add(x);
        for(int band=0;band<2;band++)for(int col=0;col<5;col++){
            int id=band*5+col;float x=left+col*bw,y=top+band*(gh+gap);
            p.setColor(Color.rgb(248,251,253));p.setStyle(Paint.Style.FILL);c.drawRect(x,y,x+bw,y+gh,p);
            p.setColor(blue);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.5f);c.drawRect(x,y,x+bw,y+gh,p);p.setStyle(Paint.Style.FILL);
            c.drawRect(x,y,x+bw,y+head,p);p.setColor(Color.WHITE);p.setTextSize(10);p.setTypeface(Typeface.DEFAULT_BOLD);center(c,p,"BLOCO "+(id+1),x+bw/2,y+19);
            for(int j=0;j<5;j++){
                int n=BLOCKS[id][j];float cx=x+bw/2,cy=y+head+rowH*(j+.5f);
                p.setColor(marked.contains(n)?Color.rgb(226,243,232):Color.WHITE);c.drawCircle(cx,cy,12,p);
                p.setColor(marked.contains(n)?green:Color.rgb(211,219,228));p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(marked.contains(n)?2.5f:.65f);c.drawCircle(cx,cy,12,p);p.setStyle(Paint.Style.FILL);
                p.setColor(marked.contains(n)?green:dark);p.setTextSize(11);p.setTypeface(marked.contains(n)?Typeface.DEFAULT_BOLD:Typeface.DEFAULT);center(c,p,String.format(java.util.Locale.US,"%02d",n),cx,cy+4);
            }
        }
        float y=top+2*gh+gap+27;
        p.setColor(dark);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(13);center(c,p,"TREVOS - MARCADOS EM VERDE",297,y);
        HashSet<Integer> ts=new HashSet<>();for(int t:trevos)ts.add(t);
        for(int t=1;t<=6;t++){
            float cx=297+(t-3.5f)*73,cy=y+36;
            p.setColor(ts.contains(t)?Color.rgb(226,243,232):Color.WHITE);c.drawCircle(cx,cy,18,p);
            p.setColor(ts.contains(t)?green:blue);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(ts.contains(t)?3f:1f);c.drawCircle(cx,cy,18,p);p.setStyle(Paint.Style.FILL);
            p.setColor(ts.contains(t)?green:dark);p.setTextSize(14);center(c,p,Integer.toString(t),cx,cy+5);
        }
        StringBuilder game=new StringBuilder();for(int n:chosen){if(game.length()>0)game.append(" - ");game.append(String.format(java.util.Locale.US,"%02d",n));}
        p.setColor(green);p.setTextSize(15);center(c,p,game.toString(),297,y+88);
        p.setTextSize(13);center(c,p,"TREVOS: "+trevos[0]+" e "+trevos[1],297,y+110);
        p.setColor(dark);p.setTypeface(Typeface.DEFAULT);p.setTextSize(9);center(c,p,"Concursos: "+contests+" | Ultimo: "+lastContest+" | Jogos: "+examined,297,y+136);
        center(c,p,"Pontuacao: "+score,297,y+152);
        p.setTextSize(8);center(c,p,"Classificacao historica nao aumenta a chance matematica de acerto.",297,803);
        center(c,p,"Volante de estudo - nao oficial.",297,818);
        pdf.finishPage(page);
        try(FileOutputStream out=new FileOutputStream(file)){pdf.writeTo(out);}finally{pdf.close();}
    }
    private void center(Canvas c,Paint p,String s,float x,float y){c.drawText(s,x-p.measureText(s)/2,y,p);}
}
