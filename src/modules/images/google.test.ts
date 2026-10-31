import { describe, expect, it } from "vitest";

import { mapGoogleImages } from "./google.ts";

describe("mapGoogleImages", () => {
  it("reads image results", () => {
    const images = mapGoogleImages({
      kind: "customsearch#search",
      items: [
        {
          title: "A cat",
          link: "https://cdn.example.com/cat.jpg",
          displayLink: "example.com",
          image: { contextLink: "https://example.com/cats", thumbnailLink: "t.jpg" },
        },
        { link: "https://cdn.example.com/dog.jpg" },
      ],
    });
    expect(images).toEqual([
      {
        title: "A cat",
        url: "https://cdn.example.com/cat.jpg",
        source: "example.com",
        pageUrl: "https://example.com/cats",
      },
      {
        title: "No title",
        url: "https://cdn.example.com/dog.jpg",
        source: "",
        pageUrl: "https://cdn.example.com/dog.jpg",
      },
    ]);
  });

  it("reads a response without results", () => {
    expect(mapGoogleImages({ kind: "customsearch#search" })).toEqual([]);
  });
});
