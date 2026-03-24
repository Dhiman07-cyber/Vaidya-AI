import type { NextApiRequest, NextApiResponse } from 'next';
import http from 'http';

export const config = {
  api: {
    bodyParser: false, // Do not parse body to allow for raw piping
    externalResolver: true,
  },
};

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  return new Promise<void>((resolve, reject) => {
    try {
      // Remove '/api' from the incoming URL, replace with backend API target
      const targetUrlString = `http://127.0.0.1:8000${req.url}`;
      const targetUrl = new URL(targetUrlString);

      const options: http.RequestOptions = {
        hostname: targetUrl.hostname,
        port: targetUrl.port,
        path: targetUrl.pathname + targetUrl.search,
        method: req.method,
        headers: {
          ...req.headers,
          host: targetUrl.host, // Must override host header for backend router
        },
        timeout: 120000, // Generous 2-minute timeout for AI generation
      };

      const proxyReq = http.request(options, (proxyRes) => {
        // Forward status and headers
        res.writeHead(proxyRes.statusCode || 500, proxyRes.headers);
        
        // Pipe the backend response stream directly to the frontend
        proxyRes.pipe(res);
        
        proxyRes.on('end', () => resolve());
      });

      proxyReq.on('error', (err: NodeJS.ErrnoException) => {
        console.error('API Proxy Error:', err);
        if (!res.headersSent) {
          res.status(502).json({ detail: 'Bad Gateway connecting to Backend', error: err.message });
        }
        res.end();
        resolve();
      });

      proxyReq.on('timeout', () => {
        console.error('API Proxy Timeout');
        if (!res.headersSent) {
          res.status(504).json({ detail: 'Backend Timeout' });
        }
        proxyReq.destroy();
        res.end();
        resolve();
      });

      // Pipe the incoming request stream (e.g. POST JSON body) to the backend
      req.pipe(proxyReq);
      
      req.on('error', (err) => {
        proxyReq.destroy();
        resolve();
      });
      
    } catch (e: any) {
      console.error('API Proxy exception:', e);
      if (!res.headersSent) {
        res.status(500).json({ detail: 'Internal Proxy Error', error: e.message });
      }
      res.end();
      resolve();
    }
  });
}
