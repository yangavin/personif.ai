import { NextRequest, NextResponse } from "next/server";

const JSONBIN_API_KEY = process.env.JSONBIN_API_KEY;
const JSONBIN_BIN_ID = process.env.JSONBIN_BIN_ID;

export async function POST(request: NextRequest) {
  try {
    if (!JSONBIN_API_KEY || !JSONBIN_BIN_ID) {
      return NextResponse.json(
        { error: "JSONBin configuration missing" },
        { status: 500 }
      );
    }

    const { personificationId } = await request.json();

    // First, get the current data
    const getCurrentResponse = await fetch(
      `https://api.jsonbin.io/v3/b/${JSONBIN_BIN_ID}`,
      {
        method: "GET",
        headers: {
          "X-Master-Key": JSONBIN_API_KEY,
          "X-Bin-Meta": "false",
        },
      }
    );

    if (!getCurrentResponse.ok) {
      throw new Error(
        `JSONBin API error: ${getCurrentResponse.status} ${getCurrentResponse.statusText}`
      );
    }

    const currentData = await getCurrentResponse.json();

    // Update the choice field
    const updatedData = {
      ...currentData,
      choice: personificationId,
    };

    // Update the bin with new choice
    const updateResponse = await fetch(
      `https://api.jsonbin.io/v3/b/${JSONBIN_BIN_ID}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-Master-Key": JSONBIN_API_KEY,
        },
        body: JSON.stringify(updatedData),
      }
    );

    if (!updateResponse.ok) {
      throw new Error(
        `JSONBin API error: ${updateResponse.status} ${updateResponse.statusText}`
      );
    }

    return NextResponse.json({
      success: true,
      activeChoice: personificationId,
    });
  } catch (error) {
    console.error("Error updating active personification:", error);
    return NextResponse.json(
      { error: "Failed to update active personification" },
      { status: 500 }
    );
  }
}
