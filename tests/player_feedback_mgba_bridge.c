/* Reconstructed native QA bridge after workspace replacement. */
#define eb_open feedback_base_open
#include "../tools/mgba_bridge.c"
#undef eb_open
#include <mgba/internal/gba/gba.h>
static unsigned feedback_errors,feedback_crashes;
static void feedback_log(struct mLogger*l,int c,enum mLogLevel lev,const char*fmt,va_list ap){
    (void)l;(void)c;if(lev&(mLOG_FATAL|mLOG_ERROR)){feedback_errors++;vfprintf(stderr,fmt,ap);fputc('\n',stderr);}
}
static struct mLogger feedback_logger={.log=feedback_log};
static void feedback_crash(void*context){(void)context;feedback_crashes++;}
void*eb_open(const char*path){
    void*v=feedback_base_open(path);feedback_errors=feedback_crashes=0;
    mLogSetDefaultLogger(&feedback_logger);
    if(v){struct mCoreCallbacks cb={0};cb.coreCrashed=feedback_crash;((struct Session*)v)->core->addCoreCallbacks(((struct Session*)v)->core,&cb);}
    return v;
}
unsigned eb_faults(void*v){(void)v;return feedback_errors+feedback_crashes;}
void eb_bytes(void*v,uint32_t address,uint8_t*out,unsigned count){
    struct Session*s=v;unsigned i;for(i=0;i<count;i++)out[i]=s->core->busRead8(s->core,address+i);
}
unsigned eb_io16(void*v,unsigned offset){
    struct Session*s=v;struct GBA*gba=s->core->board;return gba->memory.io[(offset&1023)/2];
}
int eb_save(void*v,const char*path){
    struct Session*s=v;void*bytes=NULL;size_t n=s->core->savedataClone(s->core,&bytes);
    if(!n||!bytes)return 0;FILE*f=fopen(path,"wb");if(!f){free(bytes);return 0;}
    int ok=fwrite(bytes,1,n,f)==n;ok=fclose(f)==0&&ok;free(bytes);return ok;
}
