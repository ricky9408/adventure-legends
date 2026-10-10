#include <string.h>
#include <assert.h>
#include "feedback_world.h"
unsigned short feedback_pixels[240*160/2];
unsigned short *screen=feedback_pixels;
int world_mask_active;
static int l,t,r,b;
int game_world_rect_hidden(int x,int y,int w,int h){return world_mask_active&&x>=l&&y>=t&&x+w<=r&&y+h<=b;}
void feedback_clear(unsigned c){memset(feedback_pixels,(int)c,sizeof feedback_pixels);}
void feedback_mask(int active,int x,int y,int xx,int yy){world_mask_active=active;l=x;t=y;r=xx;b=yy;}
#ifdef FEEDBACK_WORLD_SANITIZER_MAIN
int main(void){unsigned room;int x,y;for(room=0;room<82;room++)for(x=-241;x<=501;x+=37)for(y=-161;y<=341;y+=29){feedback_clear(77);feedback_mask(1,8,31,232,153);feedback_world_draw(room,x,y);}return 0;}
#endif
