#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <mgba-util/vfs.h>
#include <stdint.h>
#include <stdlib.h>
#include <dlfcn.h>

struct Observation {
    struct mCore *core;
    color_t pixels[240 * 160];
    unsigned crashes;
};

static unsigned errors;

static void observe_log(struct mLogger *logger, int category,
                        enum mLogLevel level, const char *format, va_list args) {
    (void)logger;
    (void)category;
    if (level & (mLOG_ERROR | mLOG_FATAL)) {
        errors++;
        vfprintf(stderr, format, args);
        fputc('\n', stderr);
    }
}

static struct mLogger observer = {.log = observe_log};

const char *trust_library_path(void) {
    Dl_info identity;
    return dladdr((void *)mCoreFind, &identity) ? identity.dli_fname : NULL;
}

static void crashed(void *context) {
    ((struct Observation *)context)->crashes++;
}

void *trust_open(const char *rom, const char *earned_save) {
    struct Observation *session = calloc(1, sizeof(*session));
    if (!session) return NULL;
    errors = 0;
    mLogSetDefaultLogger(&observer);
    session->core = mCoreFind(rom);
    if (!session->core || !session->core->init(session->core)) {
        free(session);
        return NULL;
    }
    mCoreConfigInit(&session->core->config, NULL);
    mCoreConfigSetDefaultIntValue(&session->core->config, "useBios", 0);
    mCoreConfigSetDefaultIntValue(&session->core->config, "skipBios", 1);
    mCoreConfigSetDefaultIntValue(&session->core->config, "videoSync", 0);
    mCoreConfigSetDefaultIntValue(&session->core->config, "audioSync", 0);
    mCoreLoadConfig(session->core);
    session->core->setVideoBuffer(session->core, session->pixels, 240);
    struct mCoreCallbacks callbacks = {0};
    callbacks.context = session;
    callbacks.coreCrashed = crashed;
    session->core->addCoreCallbacks(session->core, &callbacks);
    if (!mCoreLoadFile(session->core, rom)) goto failed;
    if (earned_save) {
        struct VFile *save = VFileOpen(earned_save, O_RDONLY);
        if (!save || !session->core->loadTemporarySave(session->core, save)) goto failed;
    }
    session->core->reset(session->core);
    return session;
failed:
    mCoreConfigDeinit(&session->core->config);
    session->core->deinit(session->core);
    free(session);
    return NULL;
}

void trust_close(void *handle) {
    struct Observation *session = handle;
    mCoreConfigDeinit(&session->core->config);
    session->core->deinit(session->core);
    free(session);
}

void trust_step(void *handle, unsigned keys) {
    struct Observation *session = handle;
    session->core->setKeys(session->core, keys & 1023);
    session->core->runFrame(session->core);
}

uint32_t trust_read(void *handle, uint32_t address, unsigned width) {
    struct Observation *session = handle;
    if (width == 4) return session->core->busRead32(session->core, address);
    if (width == 2) return session->core->busRead16(session->core, address);
    return session->core->busRead8(session->core, address);
}

unsigned trust_faults(void *handle) {
    return errors + ((struct Observation *)handle)->crashes;
}

void trust_rgb(void *handle, uint8_t *pixels) {
    struct Observation *session = handle;
    for (unsigned index = 0; index < 240 * 160; index++) {
        uint32_t color = session->pixels[index];
        pixels[index * 3] = color & 255;
        pixels[index * 3 + 1] = (color >> 8) & 255;
        pixels[index * 3 + 2] = (color >> 16) & 255;
    }
}
