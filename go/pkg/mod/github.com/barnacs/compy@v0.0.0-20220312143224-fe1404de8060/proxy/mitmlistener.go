package proxy

import (
	"crypto/tls"
	"net"
)

type mitmListener struct {
	c      chan net.Conn
	cf     *certFaker
	config *tls.Config
}

func newMitmListener(cf *certFaker, config *tls.Config) *mitmListener {
	return &mitmListener{
		c:      make(chan net.Conn),
		cf:     cf,
		config: config,
	}
}

func (l *mitmListener) Accept() (net.Conn, error) {
	return <-l.c, nil
}

func (l *mitmListener) Close() error {
	return nil
}

func (l *mitmListener) Addr() net.Addr {
	return nil
}

func (l *mitmListener) Serve(conn net.Conn, host string) (net.Conn, error) {
	sconn, err := tls.Dial("tcp", host, l.config)
	if err != nil {
		return nil, err
	}
	fakeCert, err := l.cf.FakeCert(sconn.ConnectionState().PeerCertificates[0])
	if err != nil {
		sconn.Close()
		return nil, err
	}
	tlsconf := &tls.Config{Certificates: []tls.Certificate{*fakeCert}}
	l.c <- tls.Server(conn, tlsconf)
	return sconn, nil
}
