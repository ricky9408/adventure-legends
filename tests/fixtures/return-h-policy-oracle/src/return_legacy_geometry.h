#ifndef EMBERBOND_RETURN_LEGACY_GEOMETRY_H
#define EMBERBOND_RETURN_LEGACY_GEOMETRY_H
/* Read-only descriptions of the actual historical OBJ placements. The callback
 * must not change effect/combat state. Pixel arrays are immutable ROM assets;
 * procedural kinds exactly reproduce the old upload's nontransparent pixels. */
enum { RETURN_LEGACY_PIXELS,RETURN_LEGACY_SPARK,RETURN_LEGACY_ARMOR,
       RETURN_LEGACY_DROP,RETURN_LEGACY_PIN_DOWN,RETURN_LEGACY_PIN_UP,
       RETURN_LEGACY_PIN_LEFT,RETURN_LEGACY_PIN_RIGHT };
typedef struct {const unsigned char *pixels;short x,y;unsigned char size,kind;} ReturnLegacyPiece;
typedef void (*ReturnLegacyEmit)(void *context,const ReturnLegacyPiece *piece);
static inline void return_legacy_piece(ReturnLegacyEmit emit,void *context,
 const unsigned char *pixels,int x,int y,unsigned size,unsigned kind){
 ReturnLegacyPiece p;p.pixels=pixels;p.x=(short)x;p.y=(short)y;
 p.size=(unsigned char)size;p.kind=(unsigned char)kind;emit(context,&p);
}
/* Optional for old focused harnesses. A true same-call rectangle certificate
 * proves both endpoints and every side cell of any contained raster clear.
 * False means no shortcut: callers retain their original collision semantics.
 * The implementation admits Return rooms only and owns no cached state. */
extern int return_legacy_box_certificate(int x,int y,int tx,int ty) __attribute__((weak));
static inline int return_legacy_box_clear(int x,int y,int tx,int ty){
 return return_legacy_box_certificate&&return_legacy_box_certificate(x,y,tx,ty);
}
#endif
