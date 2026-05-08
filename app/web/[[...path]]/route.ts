import { NextRequest, NextResponse } from "next/server";

const KIMI_CLI_URL = process.env.KIMI_CLI_URL || "http://kimi-cli-a5jcf4:8000";
const KIMI_API_KEY = process.env.KIMI_API_KEY || "kimi-service-secret-key-2024";

// This route proxies all requests to /web/* to the kimi-cli service
// The path structure is: /web/{userId}/{repoName}/{*path}

export async function GET(request: NextRequest) {
  return proxyRequest(request, "GET");
}

export async function POST(request: NextRequest) {
  return proxyRequest(request, "POST");
}

export async function PUT(request: NextRequest) {
  return proxyRequest(request, "PUT");
}

export async function DELETE(request: NextRequest) {
  return proxyRequest(request, "DELETE");
}

export async function PATCH(request: NextRequest) {
  return proxyRequest(request, "PATCH");
}

export async function HEAD(request: NextRequest) {
  return proxyRequest(request, "HEAD");
}

export async function OPTIONS(request: NextRequest) {
  return proxyRequest(request, "OPTIONS");
}

async function proxyRequest(request: NextRequest, method: string) {
  try {
    // Extract the path from the URL
    const url = new URL(request.url);
    const path = url.pathname.replace(/^\/web/, "");
    const searchParams = url.search;
    
    // Construct the target URL
    const targetUrl = `${KIMI_CLI_URL}/web${path}${searchParams}`;
    
    console.log(`Proxying ${method} ${url.pathname} -> ${targetUrl}`);
    
    // Prepare headers
    const headers: Record<string, string> = {
      "X-API-Key": KIMI_API_KEY,
    };
    
    // Copy relevant headers from the original request
    const relevantHeaders = [
      "accept",
      "accept-language",
      "content-type",
      "user-agent",
      "cache-control",
      "if-none-match",
      "if-modified-since",
    ];
    
    for (const header of relevantHeaders) {
      const value = request.headers.get(header);
      if (value) {
        headers[header] = value;
      }
    }
    
    // Prepare body for non-GET/HEAD requests
    let body: BodyInit | undefined;
    if (method !== "GET" && method !== "HEAD") {
      const contentType = request.headers.get("content-type");
      if (contentType?.includes("application/json")) {
        body = JSON.stringify(await request.json());
      } else if (contentType?.includes("multipart/form-data")) {
        body = await request.formData();
      } else if (contentType?.includes("application/x-www-form-urlencoded")) {
        body = await request.text();
      } else {
        body = await request.blob();
      }
    }
    
    // Make the proxy request
    const response = await fetch(targetUrl, {
      method,
      headers,
      body,
      redirect: "manual",
    });
    
    // Create the response
    const responseHeaders: Record<string, string> = {};
    
    // Copy relevant response headers
    const responseHeadersToCopy = [
      "content-type",
      "content-length",
      "cache-control",
      "etag",
      "last-modified",
      "x-kimi-web",
    ];
    
    for (const header of responseHeadersToCopy) {
      const value = response.headers.get(header);
      if (value) {
        responseHeaders[header] = value;
      }
    }
    
    // Handle redirects
    if (response.status >= 300 && response.status < 400) {
      const location = response.headers.get("location");
      if (location) {
        // Rewrite the location header to point to our proxy
        const newLocation = location.replace(
          /^https?:\/\/[^\/]+/,
          `https://kimi.x.moonsbow.com/web${path.split("/").slice(0, 3).join("/")}`
        );
        responseHeaders["location"] = newLocation;
      }
    }
    
    const responseBody = await response.arrayBuffer();
    
    return new NextResponse(responseBody, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error("Proxy error:", error);
    return NextResponse.json(
      { error: "Error proxying request to Kimi Web" },
      { status: 500 }
    );
  }
}
