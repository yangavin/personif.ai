import { NextRequest, NextResponse } from "next/server";

const JSONBIN_API_KEY = process.env.JSONBIN_API_KEY;
const JSONBIN_BIN_ID = process.env.JSONBIN_BIN_ID;

if (!JSONBIN_API_KEY || !JSONBIN_BIN_ID) {
  console.error(
    "Missing JSONBin configuration. Please set JSONBIN_API_KEY and JSONBIN_BIN_ID in your environment variables."
  );
}

export async function GET() {
  try {
    if (!JSONBIN_API_KEY || !JSONBIN_BIN_ID) {
      return NextResponse.json(
        { error: "JSONBin configuration missing" },
        { status: 500 }
      );
    }

    const response = await fetch(
      `https://api.jsonbin.io/v3/b/${JSONBIN_BIN_ID}`,
      {
        method: "GET",
        headers: {
          "X-Master-Key": JSONBIN_API_KEY,
          "X-Bin-Meta": "false",
        },
      }
    );

    if (!response.ok) {
      throw new Error(
        `JSONBin API error: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();

    return NextResponse.json({
      personifications: data.personifications || [],
      activeChoice: data.choice || null,
    });
  } catch (error) {
    console.error("Error fetching personifications:", error);
    return NextResponse.json(
      { error: "Failed to fetch personifications" },
      { status: 500 }
    );
  }
}
