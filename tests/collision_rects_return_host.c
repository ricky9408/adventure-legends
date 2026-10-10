/* Use the real Return runtime and its real private settings. No copied dynamic
 * rectangle definitions or independent reconstruction of its foot predicate. */
#include "../src/return_game.c"
void collision_return_state(unsigned a,unsigned b,unsigned c,unsigned unrelated){
 setting[0]=(unsigned char)a;setting[1]=(unsigned char)b;setting[2]=(unsigned char)c;
 setting[3]=(unsigned char)unrelated;setting[4]=(unsigned char)(unrelated*7);setting[5]=(unsigned char)(unrelated*13);
}
void collision_return_copy(unsigned char out[6]){
 unsigned i;for(i=0;i<6;i++)out[i]=setting[i];
}
