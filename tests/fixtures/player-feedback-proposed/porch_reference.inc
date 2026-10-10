static COLD void reference_floor_stamp(unsigned sprite,int x,int y){
 extern unsigned short *screen;const unsigned char*p=covenants_sprites[sprite];
 int xx,yy;x-=8+camera_x;y-=15+camera_y;
 for(yy=0;yy<16;yy++)if(y+yy>=0&&y+yy<160)for(xx=0;xx<16;xx++){
  int sx=x+xx;unsigned c=p[yy*16+xx];unsigned short*v;
  if(!c||sx<0||sx>=240)continue;
  v=screen+(y+yy)*120+sx/2;
  *v=(unsigned short)(sx&1?(*v&255)|(c<<8):(*v&65280)|c);
 }
}
