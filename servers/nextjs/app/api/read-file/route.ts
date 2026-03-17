import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { sanitizeFilename } from '@/app/(presentation-generator)/utils/others';


export async function POST(request: Request) {
  try {
    const { filePath } = await request.json();
   
      const sanitizedFilePath = sanitizeFilename(filePath);
      const normalizedPath = path.normalize(sanitizedFilePath);
      
      const allowedBaseDirs = [
        process.env.APP_DATA_DIRECTORY,
        process.env.TEMP_DIRECTORY,
        os.tmpdir(),
        // Add current directory for dev environment
        process.cwd()
      ].filter(Boolean) as string[];

      const resolvedPath = fs.realpathSync(path.resolve(normalizedPath));
      
      const isPathAllowed = allowedBaseDirs.some(baseDir => {
        try {
          const resolvedBaseDir = fs.realpathSync(path.resolve(baseDir));
          // Case insensitive check for Windows
          if (process.platform === 'win32') {
             return resolvedPath.toLowerCase().startsWith(resolvedBaseDir.toLowerCase());
          }
          return resolvedPath.startsWith(resolvedBaseDir);
        } catch (e) {
          // If a base dir doesn't exist, just ignore it
          return false;
        }
      });

    if (!isPathAllowed) {
      console.error('Unauthorized file access attempt:', resolvedPath);
      console.error('Allowed base dirs:', allowedBaseDirs);
      return NextResponse.json(
        { error: 'Access denied: File path not allowed' },
        { status: 403 }
      );
    }
    const content=  fs.readFileSync(resolvedPath, 'utf-8');
    
    return NextResponse.json({ content });
  } catch (error) {
    console.error('Error reading file:', error);
    return NextResponse.json(
      { error: 'Failed to read file' },
      { status: 500 }
    );
  }
} 