db = db.getSiblingDB("amazon_metadata"); 

db.createCollection("products", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["id", "asin", "title", "group"],
      properties: {
        id: { bsonType: "int" },
        asin: { bsonType: "string" },
        title: { bsonType: "string" },
        group: { bsonType: "string" },
        salesrank: { bsonType: ["int", "null"] },
        similar_count: { bsonType: "int" },
        similar_asins: {
          bsonType: "array",
          items: { bsonType: "string" }
        },
        categories: {
          bsonType: "array",
          items: {
            bsonType: "array",
            items: {
              bsonType: "object",
              required: ["id", "name"],
              properties: {
                id: { bsonType: "int" },
                name: { bsonType: "string" }
              }
            }
          }
        },
        reviews_summary: {
          bsonType: "object",
          properties: {
            total: { bsonType: "int" },
            downloaded: { bsonType: "int" },
            avg_rating: { bsonType: "double" }
          }
        },
        reviews: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["date", "customer_id", "rating"],
            properties: {
              date: { bsonType: "string" },
              customer_id: { bsonType: "string" },
              rating: { bsonType: "int" },
              votes: { bsonType: "int" },
              helpful: { bsonType: "int" }
            }
          }
        }
      }
    }
  },
  validationLevel: "strict",
  validationAction: "error"
});

print("Collection 'products' successfully created with strict schema validation.");