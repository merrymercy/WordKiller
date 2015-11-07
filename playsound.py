def playMP3( filename ):
    import pymedia.muxer as muxer
    import pymedia.audio.acodec as acodec
    import pymedia.audio.sound as sound

    f = open( filename, 'rb' ) 
    data= f.read( 10000 )
    dm = muxer.Demuxer( 'mp3' )
    frames = dm.parse( data )
    dec = acodec.Decoder( dm.streams[ 0 ] )
    frame = frames[0]
    r = dec.decode( frame[ 1 ] )
    snd = sound.Output( r.sample_rate, r.channels, sound.AFMT_S16_LE )
    if r: snd.play( r.data )

    while True:
        data = f.read(512)
        if len(data)>0:
            r = dec.decode( data )
            if r: snd.play( r.data )
        else:
            break
    return snd

import time
snd = playMP3( 'apology.mp3' )
while snd.isPlaying(): time.sleep( .5 )

