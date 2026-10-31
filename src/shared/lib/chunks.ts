/** SQLite allows at most 32766 bound parameters per statement, so long ID lists go in chunks. */
const SQL_CHUNK_SIZE = 10_000;

export const chunks = <T>(items: readonly T[], size = SQL_CHUNK_SIZE): T[][] =>
  Array.from({ length: Math.ceil(items.length / size) }, (_, index) =>
    items.slice(index * size, (index + 1) * size),
  );
