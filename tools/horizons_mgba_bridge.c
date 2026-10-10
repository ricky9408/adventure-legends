/* Thin testing interface around the real mGBA 0.10 core. */
#include <mgba/flags.h>
#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <mgba-util/vfs.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

struct Capture { struct mAVStream stream; FILE *file; unsigned rate, bytes; };
struct Session { struct mCore *core; color_t pixels[240*160]; struct Capture capture; };
static void audio_rate(struct mAVStream *stream, unsigned rate) {
    ((struct Capture*)stream)->rate = rate;
}
static void audio_sample(struct mAVStream *stream, int16_t left, int16_t right) {
    struct Capture *c = (struct Capture*)stream;
    if(!c->file) return;
    unsigned char bytes[4] = {left & 255, (left >> 8) & 255, right & 255, (right >> 8) & 255};
    c->bytes += fwrite(bytes, 1, 4, c->file);
}
static void put32(unsigned char *p, uint32_t v) {
    p[0]=v; p[1]=v>>8; p[2]=v>>16; p[3]=v>>24;
}
unsigned eb_audio_stop(void *v) {
    struct Session *s=v; struct Capture *c=&s->capture; if(!c->file) return 0;
    s->core->setAVStream(s->core, NULL);
    unsigned char h[44]={0};
    memcpy(h,"RIFF",4);put32(h+4,c->bytes+36);memcpy(h+8,"WAVEfmt ",8);
    put32(h+16,16);h[20]=1;h[22]=2;put32(h+24,c->rate);put32(h+28,c->rate*4);
    h[32]=4;h[34]=16;memcpy(h+36,"data",4);put32(h+40,c->bytes);
    fseek(c->file,0,SEEK_SET);fwrite(h,1,44,c->file);fclose(c->file);c->file=NULL;
    return c->bytes/4;
}
int eb_audio_start(void *v, const char *path) {
    struct Session *s=v; eb_audio_stop(v); struct Capture *c=&s->capture;
    memset(c,0,sizeof(*c));c->file=fopen(path,"wb");if(!c->file)return 0;
    unsigned char h[44]={0};fwrite(h,1,44,c->file);c->rate=32768;
    c->stream.audioRateChanged=audio_rate;c->stream.postAudioFrame=audio_sample;
    s->core->setAVStream(s->core,&c->stream);return 1;
}
static void quiet_log(struct mLogger *l, int c, enum mLogLevel lev, const char *fmt, va_list ap) {
    (void)l; (void)c;
    if (lev & (mLOG_FATAL | mLOG_ERROR)) { vfprintf(stderr, fmt, ap); fputc('\n', stderr); }
}
static struct mLogger logger = {.log = quiet_log};
void *eb_open(const char *rom) {
    struct Session *s = calloc(1, sizeof(*s));
    if (!s) return NULL;
    mLogSetDefaultLogger(&logger);
    s->core = mCoreFind(rom);
    if (!s->core) { free(s); return NULL; }
    if (!s->core->init(s->core)) { free(s); return NULL; }
    mCoreConfigInit(&s->core->config, NULL);
    mCoreConfigSetDefaultIntValue(&s->core->config, "useBios", 0);
    mCoreConfigSetDefaultIntValue(&s->core->config, "skipBios", 1);
    mCoreConfigSetDefaultIntValue(&s->core->config, "videoSync", 0);
    mCoreConfigSetDefaultIntValue(&s->core->config, "audioSync", 0);
    mCoreConfigSetDefaultIntValue(&s->core->config, "volume", 256);
    mCoreConfigSetDefaultIntValue(&s->core->config, "mute", 0);
    mCoreLoadConfig(s->core);
    s->core->setVideoBuffer(s->core, s->pixels, 240);
    if (!mCoreLoadFile(s->core, rom)) {
        mCoreConfigDeinit(&s->core->config); s->core->deinit(s->core); free(s); return NULL;
    }
    s->core->reset(s->core);
    return s;
}
void eb_close(void *v) {
    struct Session *s=v; if (!s) return;
    eb_audio_stop(v);
    mCoreConfigDeinit(&s->core->config); s->core->deinit(s->core); free(s);
}
void eb_frames(void *v, unsigned n, unsigned keys) {
    struct Session *s=v; s->core->setKeys(s->core, keys & 1023);
    while(n--) s->core->runFrame(s->core);
}
uint32_t eb_read(void *v, uint32_t address, unsigned width) {
    struct Session *s=v;
    if(width==4) return s->core->busRead32(s->core, address);
    if(width==2) return s->core->busRead16(s->core, address);
    return s->core->busRead8(s->core, address);
}
void eb_rgb(void *v, uint8_t *rgb) {
    struct Session *s=v;
    for(unsigned i=0;i<240*160;i++) {
        uint32_t p=s->pixels[i];
        rgb[3*i] = p & 255; rgb[3*i+1] = (p>>8)&255; rgb[3*i+2] = (p>>16)&255;
    }
}
unsigned eb_framecounter(void *v) { struct Session *s=v; return s->core->frameCounter(s->core); }
void eb_reset(void *v) { struct Session *s=v; s->core->reset(s->core); }
int eb_load_save(void *v,const char *path) {
    struct Session *s=v; struct VFile *vf=VFileOpen(path,O_RDONLY); if(!vf) return 0;
    return s->core->loadTemporarySave(s->core,vf);
}
/* Native core save export. This cannot import machine state or modify game RAM. */
int eb_save(void *v, const char *path) {
    struct Session *s=v; void *bytes=NULL;
    size_t n=s->core->savedataClone(s->core,&bytes);
    if(!n||!bytes) return 0;
    FILE *f=fopen(path,"wb"); if(!f){free(bytes);return 0;}
    int ok=fwrite(bytes,1,n,f)==n; ok=fclose(f)==0&&ok;free(bytes);return ok;
}
