package transcoder

import (
	"github.com/barnacs/compy/proxy"
	"github.com/chai2010/webp"
	"github.com/pixiv/go-libjpeg/jpeg"
	"net/http"
	"strconv"
)

type Jpeg struct {
	decOptions *jpeg.DecoderOptions
	encOptions *jpeg.EncoderOptions
}

func NewJpeg(quality int) *Jpeg {
	return &Jpeg{
		decOptions: &jpeg.DecoderOptions{},
		encOptions: &jpeg.EncoderOptions{
			Quality:        quality,
			OptimizeCoding: true,
		},
	}
}

func (t *Jpeg) Transcode(w *proxy.ResponseWriter, r *proxy.ResponseReader, headers http.Header) error {
	img, err := jpeg.Decode(r, t.decOptions)
	if err != nil {
		return err
	}

	encOptions := t.encOptions
	qualityString := headers.Get("X-Compy-Quality")
	if qualityString != "" {
		if quality, err := strconv.Atoi(qualityString); err != nil {
			return err
		} else {
			encOptions.Quality = quality
		}
	}

	if SupportsWebP(headers) {
		w.Header().Set("Content-Type", "image/webp")
		options := webp.Options{
			Lossless: false,
			Quality:  float32(encOptions.Quality),
		}
		if err = webp.Encode(w, img, &options); err != nil {
			return err
		}
	} else {
		if err = jpeg.Encode(w, img, encOptions); err != nil {
			return err
		}
	}
	return nil
}
