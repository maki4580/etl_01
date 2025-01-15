node.jsでExcelJSを使用してPostgreSQＬからデータを取得してExcelに出力したり、逆にExcelに入力されたデータをPostgreSQLに登録するプログラムを作成する。
Excelに出力する際は、テンプレートとして用意したシート保護されたExcelブックを使用し、取得したレコード数分の行を増やして罫線を引き、入力可能とする特定セルのみロックを解除して出力する。
-------
はい、承知いたしました。Node.jsとExcelJS、そしてPostgreSQLを連携させて、ご要望のExcel出力とデータ登録を行うプログラムの作成手順とコード例を以下に示します。

**前提条件**

*   Node.jsとnpmがインストールされていること
*   PostgreSQLがインストールされ、アクセス可能な状態であること
*   `exceljs`と`pg`パッケージがインストールされていること

    ```bash
    npm install exceljs pg
    ```
*   テンプレートExcelファイル（シート保護済みで特定セルのみロック解除）が用意されていること
    *   例：`template.xlsx`
        *   シート名：`DataSheet`
        *   ヘッダー行（1行目）は固定
        *   2行目以降にデータを出力
        *   出力対象のセルはロック解除済み（例：A2, B2, C2など）

**プログラムの構成**

1.  **データベース接続設定:** PostgreSQLへの接続設定を定義
2.  **データ取得処理:** PostgreSQLからデータを取得する関数
3.  **Excel出力処理:** テンプレートExcelを読み込み、データを書き込み、シート保護を解除/再設定する関数
4.  **データ登録処理:** Excelからデータを読み込み、PostgreSQLに登録する関数
5.  **メイン処理:** 各関数を呼び出し、処理を実行

**コード例 (JavaScript)**

```javascript
const ExcelJS = require('exceljs');
const { Client } = require('pg');
const path = require('path');


// データベース接続設定
const dbConfig = {
    user: 'your_user',
    host: 'your_host',
    database: 'your_database',
    password: 'your_password',
    port: 5432,
};


// データ取得処理
async function fetchDataFromPostgres(query) {
    const client = new Client(dbConfig);
    try {
        await client.connect();
        const result = await client.query(query);
        return result.rows;
    } catch (err) {
        console.error("Error fetching data:", err);
        throw err;
    } finally {
        await client.end();
    }
}


// Excel出力処理
async function createExcelFromTemplate(templatePath, data, outputPath) {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(templatePath);
    const worksheet = workbook.getWorksheet('DataSheet');

    const startRow = 2; // データ出力開始行
    const dataRows = data.length;


    // データを出力
    data.forEach((row, index) => {
        const currentRow = startRow + index;
        Object.keys(row).forEach((key, colIndex) => {
            const cell = worksheet.getCell(currentRow, colIndex + 1);
            cell.value = row[key];
        });
    });

    //罫線追加(データが入る行のみ)
    for(let i = startRow; i < startRow + dataRows; i++){
      worksheet.getRow(i).eachCell((cell) => {
          cell.border = {
            top: { style: 'thin', color: { argb: 'FF000000' } },
            left: { style: 'thin', color: { argb: 'FF000000' } },
            bottom: { style: 'thin', color: { argb: 'FF000000' } },
            right: { style: 'thin', color: { argb: 'FF000000' } },
          }
        });
    }
    
    //シート保護解除
    worksheet.protect.unprotect();

    // ロックを再設定し、シート保護
    worksheet.eachRow({ includeEmpty: true }, (row, rowNumber) => {
      if (rowNumber > 1) { //ヘッダーはロック、データ行のみ処理
        row.eachCell((cell, colNumber) => {
            // 特定の列のみロックを解除。A,B,C列のみを解除すると仮定
            if (colNumber == 1 || colNumber == 2 || colNumber == 3 ) {
                cell.protection = { locked: false };
            } else {
                cell.protection = { locked: true };
            }
          });
        } else{
            row.eachCell((cell)=>{
              cell.protection = { locked: true };
            })
        }
    });

    //シート保護を設定
    worksheet.protect.protect('password', {
        selectLockedCells: true,
        selectUnlockedCells: true,
    });

    await workbook.xlsx.writeFile(outputPath);
    console.log(`Excel file created successfully at ${outputPath}`);
}


// データ登録処理
async function insertDataToPostgres(filePath, tableName) {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(filePath);
    const worksheet = workbook.getWorksheet('DataSheet');

    const headers = worksheet.getRow(1).values;
    const data = [];
    worksheet.eachRow({ skip: 1, includeEmpty: false }, (row) => { // ヘッダー行をスキップ
        const rowData = {};
        row.eachCell((cell, colNumber) => {
            rowData[headers[colNumber - 1]] = cell.value;
        });
        data.push(rowData);
    });

    const client = new Client(dbConfig);
    try {
        await client.connect();
        for (const rowData of data) {
            const columns = Object.keys(rowData);
            const values = Object.values(rowData);
            const placeholders = columns.map((_, index) => `$${index + 1}`).join(',');
            const query = `INSERT INTO ${tableName} (${columns.join(',')}) VALUES (${placeholders})`;
            await client.query(query, values);
        }
        console.log("Data inserted successfully.");
    } catch (err) {
        console.error("Error inserting data:", err);
        throw err;
    } finally {
        await client.end();
    }
}


// メイン処理
async function main() {
    try {
      // 1. データ取得
        const query = "SELECT * FROM your_table";
        const data = await fetchDataFromPostgres(query);
      
        // 2. Excel出力
        const templatePath = path.join(__dirname, 'template.xlsx');
        const outputPath = path.join(__dirname, 'output.xlsx');
        await createExcelFromTemplate(templatePath, data, outputPath);


        // 3. Excelデータ登録
        // const inputExcelPath = path.join(__dirname, 'output.xlsx');
        // const tableName = 'your_table';
        // await insertDataToPostgres(inputExcelPath, tableName);

    } catch (error) {
        console.error("An error occurred:", error);
    }
}


main();
```

**使用方法**

1.  上記のコードを`app.js`などのファイルに保存
2.  `your_user`, `your_host`, `your_database`, `your_password`, `your_table` などの設定を実際の値に置き換える
3.  `template.xlsx`をスクリプトと同じディレクトリに配置
4.  `node app.js`を実行

**注意点**

*   エラー処理は必要に応じて追加・変更してください。
*   データ登録処理はコメントアウトされているので、必要に応じて有効にしてください。
*   PostgreSQLのテーブル構造とExcelのヘッダーが一致している必要があります。
*   ロックを解除する列は、必要に応じて変更してください。
*   パスワードは適切に管理してください。

このコード例は基本的な処理を網羅していますが、実際の要件に合わせてカスタマイズが必要になる場合があります。例えば、データの型変換、日付や数値のフォーマット、より複雑なExcel操作など、必要に応じて処理を追加してください。
上記コードを参考に、ご自身の環境に合わせて調整していただければと思います。
ご不明な点がございましたら、お気軽にご質問ください。

-------

はい、承知いたしました。入力可能なセル（ロック解除されたセル）の背景色を薄い黄色に着色するよう、コードを修正します。

以下に修正後のコード例を示します。

```javascript
const ExcelJS = require('exceljs');
const { Client } = require('pg');
const path = require('path');


// データベース接続設定
const dbConfig = {
    user: 'your_user',
    host: 'your_host',
    database: 'your_database',
    password: 'your_password',
    port: 5432,
};


// データ取得処理
async function fetchDataFromPostgres(query) {
    const client = new Client(dbConfig);
    try {
        await client.connect();
        const result = await client.query(query);
        return result.rows;
    } catch (err) {
        console.error("Error fetching data:", err);
        throw err;
    } finally {
        await client.end();
    }
}


// Excel出力処理
async function createExcelFromTemplate(templatePath, data, outputPath) {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(templatePath);
    const worksheet = workbook.getWorksheet('DataSheet');

    const startRow = 2; // データ出力開始行
    const dataRows = data.length;


    // データを出力
    data.forEach((row, index) => {
        const currentRow = startRow + index;
        Object.keys(row).forEach((key, colIndex) => {
            const cell = worksheet.getCell(currentRow, colIndex + 1);
            cell.value = row[key];
        });
    });

    //罫線追加(データが入る行のみ)
    for(let i = startRow; i < startRow + dataRows; i++){
      worksheet.getRow(i).eachCell((cell) => {
          cell.border = {
            top: { style: 'thin', color: { argb: 'FF000000' } },
            left: { style: 'thin', color: { argb: 'FF000000' } },
            bottom: { style: 'thin', color: { argb: 'FF000000' } },
            right: { style: 'thin', color: { argb: 'FF000000' } },
          }
        });
    }
    
    //シート保護解除
    worksheet.protect.unprotect();

    // ロックを再設定し、シート保護
    worksheet.eachRow({ includeEmpty: true }, (row, rowNumber) => {
      if (rowNumber > 1) { //ヘッダーはロック、データ行のみ処理
        row.eachCell((cell, colNumber) => {
            // 特定の列のみロックを解除。A,B,C列のみを解除すると仮定
            if (colNumber == 1 || colNumber == 2 || colNumber == 3 ) {
                cell.protection = { locked: false };
                //背景色を薄い黄色に変更
                cell.fill = {
                  type: 'pattern',
                  pattern: 'solid',
                  fgColor: { argb: 'FFFFFF00' },
                };
            } else {
                cell.protection = { locked: true };
            }
          });
        } else{
            row.eachCell((cell)=>{
              cell.protection = { locked: true };
            })
        }
    });

    //シート保護を設定
    worksheet.protect.protect('password', {
        selectLockedCells: true,
        selectUnlockedCells: true,
    });

    await workbook.xlsx.writeFile(outputPath);
    console.log(`Excel file created successfully at ${outputPath}`);
}


// データ登録処理
async function insertDataToPostgres(filePath, tableName) {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(filePath);
    const worksheet = workbook.getWorksheet('DataSheet');

    const headers = worksheet.getRow(1).values;
    const data = [];
    worksheet.eachRow({ skip: 1, includeEmpty: false }, (row) => { // ヘッダー行をスキップ
        const rowData = {};
        row.eachCell((cell, colNumber) => {
            rowData[headers[colNumber - 1]] = cell.value;
        });
        data.push(rowData);
    });

    const client = new Client(dbConfig);
    try {
        await client.connect();
        for (const rowData of data) {
            const columns = Object.keys(rowData);
            const values = Object.values(rowData);
            const placeholders = columns.map((_, index) => `$${index + 1}`).join(',');
            const query = `INSERT INTO ${tableName} (${columns.join(',')}) VALUES (${placeholders})`;
            await client.query(query, values);
        }
        console.log("Data inserted successfully.");
    } catch (err) {
        console.error("Error inserting data:", err);
        throw err;
    } finally {
        await client.end();
    }
}


// メイン処理
async function main() {
    try {
      // 1. データ取得
        const query = "SELECT * FROM your_table";
        const data = await fetchDataFromPostgres(query);
      
        // 2. Excel出力
        const templatePath = path.join(__dirname, 'template.xlsx');
        const outputPath = path.join(__dirname, 'output.xlsx');
        await createExcelFromTemplate(templatePath, data, outputPath);


        // 3. Excelデータ登録
        // const inputExcelPath = path.join(__dirname, 'output.xlsx');
        // const tableName = 'your_table';
        // await insertDataToPostgres(inputExcelPath, tableName);

    } catch (error) {
        console.error("An error occurred:", error);
    }
}


main();
```

**変更点:**

*   `createExcelFromTemplate`関数内の、ロック解除セルを設定する箇所に、以下のコードを追加しました。
    ```javascript
    cell.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FFFFFF00' }, // 薄い黄色の設定
      };
    ```
    これにより、ロックが解除されたセルは背景色が薄い黄色になります。

**使用方法:**

変更後のコードを`app.js`に保存し、再度 `node app.js` を実行してください。出力されたExcelファイルでは、入力可能なセルが薄い黄色で表示されるようになります。

この変更により、ユーザーはどのセルが編集可能かを視覚的に把握しやすくなります。
ご不明な点がございましたら、お気軽にご質問ください。

-------

はい、承知いたしました。ご要望に従い、3層アーキテクチャ（MVCモデル）に基づいて、コードを再構成します。

**3層アーキテクチャの構成**

*   **Model (モデル):** データベースとのやり取りやデータ操作を担います。
*   **View (ビュー):** ユーザーインターフェース（ここではExcelファイル）の出力と表示を担います。
*   **Controller (コントローラー):** ユーザーからのリクエストを受け取り、モデルとビューを連携させて処理を行います。

**ファイル構成**

```
app.js        // メインのエントリーポイント
/controllers
    excelController.js  // Excel操作に関するコントローラー
    dbController.js     // DB操作に関するコントローラー
/models
    excelModel.js      // Excel操作に関するモデル
    dbModel.js         // DB操作に関するモデル
```

**各ファイルの内容**

**1. app.js (メインのエントリーポイント)**

```javascript
const excelController = require('./controllers/excelController');
const dbController = require('./controllers/dbController');

async function main() {
    try {
        // 1. データ取得とExcel出力
        await excelController.generateExcel();

        // 2. Excelデータ登録（必要に応じてコメントを外す）
        // await excelController.importData();

    } catch (error) {
        console.error("An error occurred:", error);
    }
}

main();
```

**2. controllers/excelController.js (Excel操作に関するコントローラー)**

```javascript
const excelModel = require('../models/excelModel');
const dbModel = require('../models/dbModel');
const path = require('path');

const templatePath = path.join(__dirname, '../template.xlsx');
const outputPath = path.join(__dirname, '../output.xlsx');
const inputExcelPath = path.join(__dirname, '../output.xlsx');
const tableName = 'your_table';

const excelController = {
    generateExcel: async () => {
        const query = "SELECT * FROM your_table";
        const data = await dbModel.fetchData(query);
        await excelModel.createExcel(templatePath, data, outputPath);
    },
    importData: async () => {
        await excelModel.insertData(inputExcelPath, tableName);
    }
}

module.exports = excelController;
```

**3. controllers/dbController.js (DB操作に関するコントローラー)**
```javascript
// モデルに処理を移したため、controllerではモデルを呼び出すのみとなった。
// 必要に応じてエラーハンドリングなどを追加
const dbModel = require('../models/dbModel');
```
**4. models/excelModel.js (Excel操作に関するモデル)**

```javascript
const ExcelJS = require('exceljs');


const excelModel = {
    createExcel: async (templatePath, data, outputPath) => {
        const workbook = new ExcelJS.Workbook();
        await workbook.xlsx.readFile(templatePath);
        const worksheet = workbook.getWorksheet('DataSheet');
    
        const startRow = 2;
        const dataRows = data.length;
    
        data.forEach((row, index) => {
            const currentRow = startRow + index;
            Object.keys(row).forEach((key, colIndex) => {
                const cell = worksheet.getCell(currentRow, colIndex + 1);
                cell.value = row[key];
            });
        });

        //罫線追加(データが入る行のみ)
        for(let i = startRow; i < startRow + dataRows; i++){
            worksheet.getRow(i).eachCell((cell) => {
                cell.border = {
                    top: { style: 'thin', color: { argb: 'FF000000' } },
                    left: { style: 'thin', color: { argb: 'FF000000' } },
                    bottom: { style: 'thin', color: { argb: 'FF000000' } },
                    right: { style: 'thin', color: { argb: 'FF000000' } },
                }
            });
        }
            
        worksheet.protect.unprotect();
    
        worksheet.eachRow({ includeEmpty: true }, (row, rowNumber) => {
          if (rowNumber > 1) {
            row.eachCell((cell, colNumber) => {
                if (colNumber == 1 || colNumber == 2 || colNumber == 3) {
                    cell.protection = { locked: false };
                    cell.fill = {
                        type: 'pattern',
                        pattern: 'solid',
                        fgColor: { argb: 'FFFFFF00' },
                    };
                } else {
                    cell.protection = { locked: true };
                }
              });
            } else {
              row.eachCell((cell) => {
                cell.protection = { locked: true };
              });
            }
        });
    
        worksheet.protect.protect('password', {
            selectLockedCells: true,
            selectUnlockedCells: true,
        });
    
        await workbook.xlsx.writeFile(outputPath);
        console.log(`Excel file created successfully at ${outputPath}`);
    },
    insertData: async (filePath, tableName) => {
      const workbook = new ExcelJS.Workbook();
      await workbook.xlsx.readFile(filePath);
      const worksheet = workbook.getWorksheet('DataSheet');

      const headers = worksheet.getRow(1).values;
      const data = [];
      worksheet.eachRow({ skip: 1, includeEmpty: false }, (row) => {
          const rowData = {};
          row.eachCell((cell, colNumber) => {
              rowData[headers[colNumber - 1]] = cell.value;
          });
          data.push(rowData);
      });

      await dbModel.insertData(data, tableName, headers);
  }
};
module.exports = excelModel;
```

**5. models/dbModel.js (DB操作に関するモデル)**

```javascript
const { Client } = require('pg');


// データベース接続設定
const dbConfig = {
  user: 'your_user',
  host: 'your_host',
  database: 'your_database',
  password: 'your_password',
  port: 5432,
};

const dbModel = {
  fetchData: async (query) => {
    const client = new Client(dbConfig);
    try {
      await client.connect();
      const result = await client.query(query);
      return result.rows;
    } catch (err) {
      console.error("Error fetching data:", err);
      throw err;
    } finally {
      await client.end();
    }
  },
    insertData: async (data, tableName, headers) => {
    const client = new Client(dbConfig);
    try {
        await client.connect();
        for (const rowData of data) {
            const columns = headers;
            const values = columns.map(column => rowData[column]);
            const placeholders = columns.map((_, index) => `$${index + 1}`).join(',');
            const query = `INSERT INTO ${tableName} (${columns.join(',')}) VALUES (${placeholders})`;
            await client.query(query, values);
          }
        console.log("Data inserted successfully.");
      } catch (err) {
        console.error("Error inserting data:", err);
        throw err;
      } finally {
        await client.end();
      }
  }
};

module.exports = dbModel;
```

**変更点:**

*   各機能がModel、View、Controllerの役割に分割されました。
*   データベース接続設定と関連する処理は`dbModel.js`に集約しました。
*   Excel操作に関連する処理は`excelModel.js`に集約しました。
*   ControllerはModelを呼び出し、結果を必要に応じてView（ここではファイル出力）に渡す役割を担います。

**使用方法**

1.  上記のファイル構成と内容でファイルを配置
2.  `your_user`, `your_host`, `your_database`, `your_password`, `your_table` などの設定を実際の値に置き換える
3.  `template.xlsx`をルートディレクトリに配置
4.  `node app.js`を実行

この変更により、コードの可読性と保守性が向上し、各層の役割が明確になります。
ご不明な点がございましたら、お気軽にご質問ください。

-------

はい、承知いたしました。これまで作成したNode.jsのプログラムをNext.jsで実装し直します。Next.jsはReactベースのフレームワークであり、サーバーサイドレンダリングやルーティング機能が組み込まれているため、APIエンドポイントとして機能するサーバーレス関数（API routes）を活用して、3層アーキテクチャ（MVCモデル）を実装します。

**ファイル構成**

```
nextjs-excel-app/
├── pages/
│   └── api/
│       ├── generateExcel.js   // Excel生成APIエンドポイント
│       └── importData.js     // データ登録APIエンドポイント
├── controllers/
│   ├── excelController.js    // Excel操作に関するコントローラー
│   └── dbController.js       // DB操作に関するコントローラー
├── models/
│   ├── excelModel.js         // Excel操作に関するモデル
│   └── dbModel.js            // DB操作に関するモデル
├── public/
│   └── template.xlsx        // テンプレートExcelファイル
├── package.json
├── ...
```

**各ファイルの内容**

**1. pages/api/generateExcel.js (Excel生成APIエンドポイント)**

```javascript
import excelController from '../../controllers/excelController';

export default async function handler(req, res) {
  try {
    const buffer = await excelController.generateExcel();
    
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', 'attachment; filename=output.xlsx');
    
    res.send(buffer);
  } catch (error) {
    console.error("Error generating Excel:", error);
    res.status(500).json({ message: "Failed to generate Excel file." });
  }
}
```

**2. pages/api/importData.js (データ登録APIエンドポイント)**

```javascript
import excelController from '../../controllers/excelController';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method Not Allowed' });
  }

  try {
    const data = req.body;
    await excelController.importData(data);
    res.status(200).json({ message: "Data imported successfully." });
  } catch (error) {
    console.error("Error importing data:", error);
    res.status(500).json({ message: "Failed to import data." });
  }
}

```

**3. controllers/excelController.js (Excel操作に関するコントローラー)**

```javascript
import excelModel from '../models/excelModel';
import dbModel from '../models/dbModel';
import path from 'path';
import fs from 'fs';

const templatePath = path.join(process.cwd(), 'public', 'template.xlsx'); // Next.jsではpublicフォルダを使う
const outputPath = path.join(process.cwd(), 'output.xlsx');
const tableName = 'your_table';


const excelController = {
    generateExcel: async () => {
        const query = "SELECT * FROM your_table";
        const data = await dbModel.fetchData(query);
        const buffer = await excelModel.createExcel(templatePath, data);
        return buffer;
    },
    importData: async (data) => {
       await excelModel.insertData(data, tableName);
    }
}

export default excelController;
```

**4. controllers/dbController.js (DB操作に関するコントローラー)**

```javascript
// モデルに処理を移したため、controllerではモデルを呼び出すのみとなった。
// 必要に応じてエラーハンドリングなどを追加
import dbModel from '../models/dbModel';
```

**5. models/excelModel.js (Excel操作に関するモデル)**

```javascript
const ExcelJS = require('exceljs');
import fs from 'fs';

const excelModel = {
    createExcel: async (templatePath, data) => {
        const workbook = new ExcelJS.Workbook();
        await workbook.xlsx.readFile(templatePath);
        const worksheet = workbook.getWorksheet('DataSheet');
    
        const startRow = 2;
        const dataRows = data.length;
    
        data.forEach((row, index) => {
            const currentRow = startRow + index;
            Object.keys(row).forEach((key, colIndex) => {
                const cell = worksheet.getCell(currentRow, colIndex + 1);
                cell.value = row[key];
            });
        });

        //罫線追加(データが入る行のみ)
        for(let i = startRow; i < startRow + dataRows; i++){
            worksheet.getRow(i).eachCell((cell) => {
                cell.border = {
                    top: { style: 'thin', color: { argb: 'FF000000' } },
                    left: { style: 'thin', color: { argb: 'FF000000' } },
                    bottom: { style: 'thin', color: { argb: 'FF000000' } },
                    right: { style: 'thin', color: { argb: 'FF000000' } },
                }
            });
        }
            
        worksheet.protect.unprotect();
    
        worksheet.eachRow({ includeEmpty: true }, (row, rowNumber) => {
          if (rowNumber > 1) {
            row.eachCell((cell, colNumber) => {
                if (colNumber == 1 || colNumber == 2 || colNumber == 3) {
                    cell.protection = { locked: false };
                    cell.fill = {
                        type: 'pattern',
                        pattern: 'solid',
                        fgColor: { argb: 'FFFFFF00' },
                    };
                } else {
                    cell.protection = { locked: true };
                }
              });
            } else {
              row.eachCell((cell) => {
                cell.protection = { locked: true };
              });
            }
        });
    
        worksheet.protect.protect('password', {
            selectLockedCells: true,
            selectUnlockedCells: true,
        });
        const buffer = await workbook.xlsx.writeBuffer();
        return buffer;
    },
  
    insertData: async (data, tableName) => {
       const workbook = new ExcelJS.Workbook();
       const worksheet = workbook.addWorksheet('DataSheet');
      const headers = Object.keys(data[0]);
      worksheet.addRow(headers);
      data.forEach(row =>{
           worksheet.addRow(Object.values(row));
       });
       const filePath = path.join(process.cwd(), 'temp.xlsx');
       await workbook.xlsx.writeFile(filePath);
       await dbModel.insertData(filePath,tableName);
      
     }
};
export default excelModel;
```

**6. models/dbModel.js (DB操作に関するモデル)**

```javascript
const { Client } = require('pg');
const ExcelJS = require('exceljs');
import path from 'path';
import fs from 'fs';


// データベース接続設定
const dbConfig = {
    user: 'your_user',
    host: 'your_host',
    database: 'your_database',
    password: 'your_password',
    port: 5432,
};

const dbModel = {
    fetchData: async (query) => {
        const client = new Client(dbConfig);
        try {
            await client.connect();
            const result = await client.query(query);
            return result.rows;
        } catch (err) {
            console.error("Error fetching data:", err);
            throw err;
        } finally {
            await client.end();
        }
    },
  insertData: async (filePath, tableName) => {
    const workbook = new ExcelJS.Workbook();
      await workbook.xlsx.readFile(filePath);
      const worksheet = workbook.getWorksheet('DataSheet');

      const headers = worksheet.getRow(1).values;
      const data = [];
      worksheet.eachRow({ skip: 1, includeEmpty: false }, (row) => {
          const rowData = {};
          row.eachCell((cell, colNumber) => {
              rowData[headers[colNumber - 1]] = cell.value;
          });
          data.push(rowData);
        });
      const client = new Client(dbConfig);
      try {
        await client.connect();
        for (const rowData of data) {
            const columns = Object.keys(rowData);
            const values = Object.values(rowData);
            const placeholders = columns.map((_, index) => `$${index + 1}`).join(',');
            const query = `INSERT INTO ${tableName} (${columns.join(',')}) VALUES (${placeholders})`;
            await client.query(query, values);
        }
        console.log("Data inserted successfully.");
    } catch (err) {
        console.error("Error inserting data:", err);
        throw err;
    } finally {
        await client.end();
    }
     fs.unlinkSync(filePath);
  }
};

export default dbModel;
```

**変更点:**

*   APIエンドポイントとして、Excel生成（`generateExcel.js`）とデータ登録（`importData.js`）を実装しました。
*   `fs`モジュールを使用して、テンプレートファイルのパスを設定しました(Next.jsでは`public`ディレクトリを使用)。
*   Excel生成APIは生成されたExcelファイルをレスポンスとして返却します。
*   データ登録APIはクライアントから送信されたJSONデータを処理します。
*   `excelModel`に`xlsx.writeBuffer()`を追加して、バッファを返却する様にしました
*    `excelModel`の`insertData`に`filePath`を渡すように変更しました
*   `dbModel`の`insertData`は一時的に作成したExcelファイルを読み込むように変更しました。
*   `dbModel`の`insertData`の最後に一時的に作成したファイルを削除するようにしました

**使用方法:**

1.  上記ファイル構成でファイルを配置します。
2.  `your_user`, `your_host`, `your_database`, `your_password`, `your_table`などの設定を実際の値に置き換えます。
3.  `template.xlsx`を `public` ディレクトリに配置します。
4.  Next.jsプロジェクトのルートディレクトリで `npm install exceljs pg` を実行して、必要なパッケージをインストールします。
5.  `npm run dev` または `yarn dev` を実行して、Next.js開発サーバーを起動します。
6.  ブラウザから `http://localhost:3000/api/generateExcel` にアクセスすると、Excelファイルがダウンロードされます。
7.  データ登録は、クライアントサイドから`http://localhost:3000/api/importData`に対してPOSTリクエストを送信してください。POSTリクエストのbodyにJson形式で送信してください
    例
    ```json
    [
        {
            "id": 1,
            "name": "test1",
            "age": 10
        },
        {
            "id": 2,
            "name": "test2",
            "age": 20
        }
    ]
    ```
この構成で、Next.jsアプリケーションとして、Excelファイルの出力とデータ登録機能がAPIエンドポイントとして利用可能になります。

**注意点**

*   この例では、ファイルアップロード機能は実装していません。
*   エラーハンドリングは必要に応じて調整してください。
*   データ登録APIにクライアントからデータを送信する実装は、別途実装してください。

このコード例はNext.jsでの実装の基本的な構成を示しています。実際のアプリケーションでは、より複雑なロジックやフロントエンドのインタラクションを追加する必要があります。
ご不明な点がございましたら、お気軽にご質問ください。

-------

はい、承知いたしました。このプログラムのシーケンス図をPlantUMLで記述します。以下に、Excel出力とデータ登録それぞれのシーケンス図を示します。

**1. Excel出力のシーケンス図**

```plantuml
@startuml
participant "Client (Browser)" as Client
participant "Next.js API\n(generateExcel.js)" as Api
participant "Controller\n(excelController.js)" as Controller
participant "Model\n(excelModel.js)" as ExcelModel
participant "Model\n(dbModel.js)" as DbModel
database "PostgreSQL" as DB

Client -> Api: HTTP GET /api/generateExcel
activate Api
    Api -> Controller: generateExcel()
    activate Controller
        Controller -> DbModel: fetchData(query)
        activate DbModel
            DbModel -> DB: SQL SELECT
            activate DB
            DB --> DbModel: Results
            deactivate DB
        DbModel --> Controller: Data
        deactivate DbModel

        Controller -> ExcelModel: createExcel(templatePath, data)
        activate ExcelModel
             ExcelModel --> ExcelModel: Read Template Excel
             ExcelModel --> ExcelModel: Write Data to Excel
             ExcelModel --> ExcelModel: Set Cell Styles & Protection
             ExcelModel --> ExcelModel: Create Excel Buffer
         ExcelModel --> Controller: Excel Buffer
         deactivate ExcelModel

    Controller --> Api: Excel Buffer
    deactivate Controller

    Api --> Client: HTTP Response (Excel file)
deactivate Api
Client -> Client: Download Excel File
@enduml
```

**2. データ登録のシーケンス図**

```plantuml
@startuml
participant "Client (Browser)" as Client
participant "Next.js API\n(importData.js)" as Api
participant "Controller\n(excelController.js)" as Controller
participant "Model\n(excelModel.js)" as ExcelModel
participant "Model\n(dbModel.js)" as DbModel
database "PostgreSQL" as DB
Client -> Api: HTTP POST /api/importData (JSON data)
activate Api
  Api -> Controller: importData(data)
  activate Controller
     Controller -> ExcelModel: insertData(data, tableName)
        activate ExcelModel
          ExcelModel --> ExcelModel: Write data to a temporary Excel
          ExcelModel -> DbModel: insertData(filePath, tableName)
            activate DbModel
                 DbModel --> DbModel: Read Temporary Excel
                 DbModel -> DB: SQL INSERT
                activate DB
                DB --> DbModel: Success or Fail
                 deactivate DB
            DbModel --> ExcelModel: Results
            deactivate DbModel

          ExcelModel --> ExcelModel: Delete Temporary Excel
          ExcelModel --> Controller:  Success
         deactivate ExcelModel
   Controller --> Api: Success
   deactivate Controller
   Api --> Client: HTTP Response (200 OK or error)
deactivate Api
@enduml
```

**解説**

*   **`participant`**: 各コンポーネント（クライアント、API、コントローラー、モデル）を表します。
*   **`database`**: データベースを表します。
*   **`->`**: メッセージの流れを表します。
*   **`-->`**: レスポンスの流れを表します。
*   **`activate`**: 処理が開始されたことを示します。
*   **`deactivate`**: 処理が終了したことを示します。
*   シーケンス図では、APIエンドポイント(`/api/generateExcel`と`/api/importData`)がリクエストを受け取り、コントローラーを介してモデルを呼び出し、データベースと通信する流れが示されています。
*  Excel出力のシーケンスでは、クライアントがExcelファイルをダウンロードする動作が表現されています
*   データ登録のシーケンスでは、ExcelModelが一時的にExcelファイルを生成し、それを読み取ってDBに登録した後、削除する流れが表現されています。

これらのシーケンス図は、プログラムの処理フローを明確にし、各コンポーネントの役割を理解するのに役立ちます。また、PlantUMLのテキスト形式なので、必要に応じて編集や共有が容易です。

ご不明な点がございましたら、お気軽にご質問ください。

-------

はい、承知いたしました。プログラムの詳細設計書をMarkdown形式で作成します。

# 詳細設計書

## 1. はじめに

このドキュメントは、Next.jsで実装されたExcel出力・データ登録プログラムの詳細設計について記述します。このプログラムは、PostgreSQLデータベースからデータを取得し、テンプレートExcelファイルに基づいてExcelファイルを出力したり、Excelファイルから読み取ったデータをPostgreSQLに登録する機能を提供します。

## 2. システム概要

### 2.1. 目的

*   PostgreSQLデータベースからデータを取得し、指定したフォーマットのExcelファイルとして出力する。
*   Excelファイルに入力されたデータをPostgreSQLデータベースに登録する。
*   Excel出力時に、特定セルのみ編集可能とし、シート保護を設定する。

### 2.2. 機能概要

*   **Excel出力機能:**
    *   PostgreSQLからデータを取得する。
    *   指定されたテンプレートExcelファイルを読み込む。
    *   取得したデータをExcelファイルに書き込む。
    *   特定のセルのみロックを解除し、背景色を薄い黄色に設定する。
    *   シート保護を設定したExcelファイルを出力する。
*   **データ登録機能:**
    *   クライアントから送信されたJSON形式のデータを受け取る。
    *   一時的にExcelファイルを作成し、データを書き込む。
    *   作成したExcelファイルからデータを読み込み、PostgreSQLに登録する。
    *   一時的に作成したExcelファイルを削除する。

### 2.3. アーキテクチャ

3層アーキテクチャ（MVCモデル）を採用します。

*   **View:**  Excelファイル（テンプレート、出力）
*   **Controller:**  APIエンドポイント (Next.jsのAPI routes)
*   **Model:**
    *   `excelModel.js`: Excelファイルの読み込み、書き込み、フォーマット設定などの操作。
    *   `dbModel.js`: PostgreSQLデータベースへの接続、データ取得、データ登録操作。

## 3. モジュール設計

### 3.1. APIエンドポイント

*   **`/api/generateExcel` (GET):**
    *   PostgreSQLからデータを取得し、Excelファイルを出力する。
    *   出力されたExcelファイルはHTTPレスポンスとして返却する。
    *   `Content-Type`を`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`に設定する。
    *   `Content-Disposition`ヘッダーを設定し、ダウンロードファイル名を`output.xlsx`とする。
*   **`/api/importData` (POST):**
    *   クライアントからJSON形式のデータを受け取り、PostgreSQLに登録する。
    *   登録成功時はステータスコード`200`とメッセージを返す。
    *   登録失敗時はステータスコード`500`とエラーメッセージを返す。

### 3.2. コントローラー (`controllers`)

*   **`excelController.js`:**
    *   `generateExcel()`:
        *   `dbModel`を使用してPostgreSQLからデータを取得する。
        *   `excelModel`を使用してExcelファイルを作成する。
        *   作成したExcelファイルをバッファ形式で返す。
    *   `importData(data)`:
       *  `excelModel`を使用してExcelファイルからデータを読み込み、PostgreSQLに登録する。
*   **`dbController.js`:**
     * モデルに処理を移したため、controllerではモデルを呼び出すのみとなった。
       必要に応じてエラーハンドリングなどを追加

### 3.3. モデル (`models`)

*   **`excelModel.js`:**
    *   `createExcel(templatePath, data)`:
        *   指定されたテンプレートExcelファイルを読み込む。
        *   取得したデータをExcelファイルに書き込む。
        *   特定のセルのみロックを解除し、背景色を薄い黄色に設定する。
        *   シート保護を設定する。
        *   Excelファイルをバッファとして返す。
    *   `insertData(data, tableName)`:
       *  クライアントから送信されたデータを一時的にExcelファイルを作成する。
       *   作成したExcelファイルを読み込み、`dbModel`に登録処理を依頼する。
*   **`dbModel.js`:**
    *   `fetchData(query)`:
        *   指定されたSQLクエリを実行し、PostgreSQLからデータを取得する。
        *   取得したデータを返す。
    *    `insertData(filePath, tableName)`:
        *  指定されたExcelファイルを読み込み、PostgreSQLにデータを登録する。
        *   一時的に作成したExcelファイルを削除する。

## 4. データ構造

### 4.1. PostgreSQL

*   テーブル構造は可変とする。
*   プログラムの設定ファイル(`dbConfig`)でテーブル名やカラムを指定する。

### 4.2. Excelファイル

*   テンプレートExcelファイル(`template.xlsx`)を用意する。
*   `DataSheet`という名前のシートを使用する。
*   ヘッダー行（1行目）は固定とする。
*   データは2行目から書き込む。
*   指定された列のみロック解除および背景色を変更する。

### 4.3. クライアントから送信されるデータ(POST時)
* JSON形式で送信する
    例
    ```json
    [
        {
            "id": 1,
            "name": "test1",
            "age": 10
        },
        {
            "id": 2,
            "name": "test2",
            "age": 20
        }
    ]
    ```
## 5. 実装詳細

### 5.1. 使用ライブラリ

*   `exceljs`: Excelファイルの読み書き、フォーマット設定に利用。
*   `pg`: PostgreSQLへの接続とクエリ実行に利用。
*   `path`: ファイルパス操作に使用。
*   `fs`: ファイルシステム操作に使用。

### 5.2. 設定ファイル

*   `dbConfig`オブジェクトに、データベースの接続情報を設定する。
    *   `user`: PostgreSQLユーザー名
    *   `host`: PostgreSQLホスト名
    *   `database`: PostgreSQLデータベース名
    *   `password`: PostgreSQLパスワード
    *   `port`: PostgreSQLポート番号

### 5.3. エラー処理

*   各モジュールで発生したエラーは、ログに出力する。
*   APIエンドポイントでエラーが発生した場合は、クライアントにエラーメッセージを返す。

## 6. その他

### 6.1. セキュリティ

*   データベースの認証情報は環境変数などから設定し、ソースコードに直接記述しないこと。
*   APIエンドポイントにアクセス制限を設けること。

### 6.2. 運用

*   Node.jsとnpmがインストールされた環境で実行すること。
*   PostgreSQLデータベースが起動していること。

この詳細設計書は、プログラムの各要素と実装の詳細を定義し、開発の指針となることを目指します。この設計書に基づいて開発を進めることで、実装の一貫性を保ち、品質の高いプログラムを提供することを目指します。

以上が、Markdown形式での詳細設計書です。
ご不明な点がございましたら、お気軽にご質問ください。

-------

はい、承知いたしました。このプログラムのAPI仕様書をMarkdown形式で作成します。

# API仕様書

## 1. はじめに

このドキュメントは、Next.jsで実装されたExcel出力・データ登録プログラムのAPI仕様を定義します。このプログラムは、PostgreSQLデータベースとの連携機能を提供し、Excelファイルの出力およびデータ登録をAPIを通じて利用可能にします。

## 2. API概要

このAPIは、以下の2つのエンドポイントを提供します。

*   **`/api/generateExcel` (GET):**
    *   PostgreSQLからデータを取得し、Excelファイルを出力します。
*   **`/api/importData` (POST):**
    *   クライアントから送信されたJSON形式のデータをPostgreSQLデータベースに登録します。

## 3. エンドポイント詳細

### 3.1. `/api/generateExcel` (GET)

#### 3.1.1. リクエスト

*   **HTTPメソッド:** `GET`
*   **リクエストヘッダー:**
    *   なし

#### 3.1.2. レスポンス

*   **成功時:**
    *   **ステータスコード:** `200 OK`
    *   **レスポンスヘッダー:**
        *   `Content-Type`: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
        *   `Content-Disposition`: `attachment; filename="output.xlsx"`
    *   **レスポンスボディ:**
        *   Excelファイル（`output.xlsx`）のバイナリデータ

*   **エラー時:**
    *   **ステータスコード:** `500 Internal Server Error`
    *   **レスポンスヘッダー:**
        *   `Content-Type`: `application/json`
    *   **レスポンスボディ:**
        ```json
        {
            "message": "Failed to generate Excel file."
        }
        ```

#### 3.1.3. 例

**リクエスト:**

```
GET /api/generateExcel
```

**レスポンス (成功時):**

*   HTTPステータスコード: `200 OK`
*   レスポンスヘッダー:
    ```
    Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    Content-Disposition: attachment; filename="output.xlsx"
    ```
*   レスポンスボディ: Excelファイルのバイナリデータ

**レスポンス (エラー時):**

*   HTTPステータスコード: `500 Internal Server Error`
*   レスポンスヘッダー:
    ```
    Content-Type: application/json
    ```
*   レスポンスボディ:
    ```json
    {
        "message": "Failed to generate Excel file."
    }
    ```

### 3.2. `/api/importData` (POST)

#### 3.2.1. リクエスト

*   **HTTPメソッド:** `POST`
*   **リクエストヘッダー:**
    *   `Content-Type`: `application/json`
*   **リクエストボディ:**
    *   登録するデータのJSON配列。
         例：
        ```json
        [
            {
                "id": 1,
                "name": "test1",
                "age": 10
            },
            {
                "id": 2,
                "name": "test2",
                "age": 20
            }
        ]
        ```

#### 3.2.2. レスポンス

*   **成功時:**
    *   **ステータスコード:** `200 OK`
    *   **レスポンスヘッダー:**
        *   `Content-Type`: `application/json`
    *   **レスポンスボディ:**
        ```json
        {
            "message": "Data imported successfully."
        }
        ```

*   **エラー時:**
    *   **ステータスコード:** `500 Internal Server Error`
    *   **レスポンスヘッダー:**
        *   `Content-Type`: `application/json`
    *   **レスポンスボディ:**
        ```json
        {
            "message": "Failed to import data."
        }
        ```

#### 3.2.3. 例

**リクエスト:**

*   HTTPメソッド: `POST`
*   リクエストヘッダー:
    ```
    Content-Type: application/json
    ```
*   リクエストボディ:
    ```json
    [
        {
            "id": 1,
            "name": "test1",
            "age": 10
        },
        {
            "id": 2,
            "name": "test2",
            "age": 20
        }
    ]
    ```
**レスポンス (成功時):**

*   HTTPステータスコード: `200 OK`
*   レスポンスヘッダー:
    ```
    Content-Type: application/json
    ```
*   レスポンスボディ:
    ```json
    {
        "message": "Data imported successfully."
    }
    ```

**レスポンス (エラー時):**

*   HTTPステータスコード: `500 Internal Server Error`
*   レスポンスヘッダー:
    ```
    Content-Type: application/json
    ```
*   レスポンスボディ:
    ```json
    {
        "message": "Failed to import data."
    }
    ```

## 4. セキュリティ

*   APIエンドポイントへのアクセス制限は、必要に応じて実装する。
*   データベース接続情報は環境変数などから設定し、ソースコードに直接記述しない。

## 5. その他

*   APIの認証や認可に関する詳細な仕様は、別途検討する。
*   APIのバージョン管理は、必要に応じて検討する。

このAPI仕様書は、プログラムのAPIインターフェースを定義し、APIを利用するクライアント開発者に必要な情報を提供するものです。この仕様に基づいてAPIを利用することで、システム連携を円滑に進めることができます。

以上が、Markdown形式でのAPI仕様書です。
ご不明な点がございましたら、お気軽にご質問ください。

=======

Next.jsとExcelJSを使用して、以下の２つのAPIを実装する。
機能1：Excelに入力された商品の注文数の一覧データをPostgreSQLに登録する。
機能2：PostgreSQLから商品の注文状況の一覧をExcelに出力する。

このプログラムは、3層アーキテクチャ（MVC）で作成する。
機能1について、以下とする。
・WebページからExcelファイルを指定し、指定されたExcelファイルはAmazon S3のuploadsプレフィックスに配置する。
・uploadsプレフィックスに配置されたExcelファイルを取得してPostgreSQLにデータ登録する。
・データ登録後は、ExcelファイルをAmazon S3のfinishedプレフィックスに配置する。
機能2について、以下とする。
・出力する際、Excelのレコード数に応じて一覧の罫線を引く。
・出力するExcelは、特定の列のデータのみ入力可能とし、それ以外のセルはロックされている状態で出力する。
・出力するExcelの入力可能セルは背景色を薄黄色に設定する。

-------

**ディレクトリ構成**

```
my-excel-app/
├── components/
│   └── FileUpload.js
├── controllers/
│   └── excelController.js
├── models/
│   └── orderModel.js
├── services/
│   ├── excelService.js
│   └── s3Service.js
├── pages/
│   └── api/
│       └── excel.js
├── .env
├── ...
└── package.json
```

**1. 環境変数設定 (.env)**

```env
DATABASE_URL=postgresql://your_user:your_password@your_host:your_port/your_database
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=your_region
AWS_BUCKET_NAME=your_bucket_name
```

**2. モデル (models/orderModel.js)**

```javascript
// models/orderModel.js
import { Pool } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export const createOrderTable = async () => {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        product_name VARCHAR(255) NOT NULL,
        quantity INTEGER NOT NULL,
        order_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } finally {
    client.release();
  }
};


export const insertOrders = async (orders) => {
  const client = await pool.connect();
  try {
      await createOrderTable();
      const query = `
      INSERT INTO orders (product_name, quantity) VALUES
      ${orders.map((_, index) => `($${index * 2 + 1}, $${index * 2 + 2})`).join(',')}
    `;
    const values = orders.flatMap(order => [order.product_name, order.quantity]);
    await client.query(query, values);
  } finally {
      client.release();
  }
};

export const fetchOrders = async () => {
  const client = await pool.connect();
  try {
    await createOrderTable();
    const result = await client.query('SELECT id, product_name, quantity, order_date FROM orders');
    return result.rows;
  } finally {
    client.release();
  }
};
```

**3. S3サービス (services/s3Service.js)**

```javascript
// services/s3Service.js
import AWS from 'aws-sdk';

AWS.config.update({
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  region: process.env.AWS_REGION,
});

const s3 = new AWS.S3();
const bucketName = process.env.AWS_BUCKET_NAME;

const uploadFileToS3 = async (file, prefix) => {
    const params = {
      Bucket: bucketName,
      Key: `${prefix}/${file.originalname}`,
      Body: file.buffer,
    };
    return s3.upload(params).promise();
  };

const getFileFromS3 = async (key) => {
  const params = {
    Bucket: bucketName,
    Key: key,
  };
  return s3.getObject(params).promise();
};

const moveFileInS3 = async (sourceKey, destinationKey) => {
  await s3.copyObject({
    Bucket: bucketName,
    CopySource: `/${bucketName}/${sourceKey}`,
    Key: destinationKey,
  }).promise();

  await s3.deleteObject({
    Bucket: bucketName,
    Key: sourceKey,
  }).promise();
};

export { uploadFileToS3, getFileFromS3, moveFileInS3 };
```

**4. Excelサービス (services/excelService.js)**

```javascript
// services/excelService.js
import ExcelJS from 'exceljs';

const INPUTABLE_COLUMN_INDEX = 2;
const HEADER = ["ID", "商品名", "注文数", "注文日時"];

const parseExcelData = async (buffer) => {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.load(buffer);
    const worksheet = workbook.getWorksheet(1);
    const rows = [];
    worksheet.eachRow((row, rowNumber) => {
      if (rowNumber === 1) return; // ヘッダー行をスキップ
       const rowValues = row.values;
        rows.push({
            product_name: rowValues[1],
            quantity: rowValues[2],
        });
    });
    return rows;
};


const createExcelFromData = async (orders) => {
  const workbook = new ExcelJS.Workbook();
  const worksheet = workbook.addWorksheet('注文一覧');
  worksheet.columns = HEADER.map(header => ({ header, key: header.toLowerCase() }));
  worksheet.addRow(HEADER);

  orders.forEach(order => {
    worksheet.addRow({
      id: order.id,
      product_name: order.product_name,
      quantity: order.quantity,
      order_date: order.order_date
    });
  });

  // 行数に合わせて罫線を設定
  const lastRow = worksheet.lastRow.number;
    for (let i = 1; i <= lastRow; i++) {
        worksheet.getRow(i).eachCell((cell) => {
            cell.border = {
                top: { style: 'thin' },
                left: { style: 'thin' },
                bottom: { style: 'thin' },
                right: { style: 'thin' }
            };
        });
    }


  // 特定列のみ入力可能にし、背景色を設定、その他をロック
  worksheet.eachRow({ includeEmpty: true }, (row) => {
    row.eachCell({ includeEmpty: true }, (cell, colNumber) => {
      if (colNumber === INPUTABLE_COLUMN_INDEX) {
        cell.fill = {
          type: 'pattern',
          pattern: 'solid',
          fgColor: { argb: 'FFFFFFE0' },
        };
        cell.protection = { locked: false };
      } else {
        cell.protection = { locked: true };
      }
    });
  });

  // シートを保護
  worksheet.protect('password', {
    selectLockedCells: true,
    selectUnlockedCells: true,
    formatCells: false,
    formatColumns: false,
    formatRows: false,
    insertColumns: false,
    insertRows: false,
    insertHyperlinks: false,
    deleteColumns: false,
    deleteRows: false,
    sort: false,
    autoFilter: false,
    pivotTables: false,
    objects: false,
    scenarios: false,
  });

    const buffer = await workbook.xlsx.writeBuffer();
    return buffer;
};

export { parseExcelData, createExcelFromData };
```

**5. コントローラ (controllers/excelController.js)**

```javascript
// controllers/excelController.js
import { insertOrders, fetchOrders } from '../models/orderModel';
import { getFileFromS3, uploadFileToS3, moveFileInS3 } from '../services/s3Service';
import { parseExcelData, createExcelFromData } from '../services/excelService';

const uploadAndProcessExcel = async (req, res) => {
  try {
      if (!req.file) {
          return res.status(400).json({ message: 'No file uploaded' });
      }

      await uploadFileToS3(req.file, 'uploads');
      const fileKey = `uploads/${req.file.originalname}`;
      const s3Object = await getFileFromS3(fileKey);
      const excelData = await parseExcelData(s3Object.Body);

      await insertOrders(excelData);
      const destinationKey = `finished/${req.file.originalname}`;
      await moveFileInS3(fileKey, destinationKey);


      res.status(200).json({ message: 'File uploaded and processed successfully' });
  } catch (error) {
    console.error('Error processing file:', error);
    res.status(500).json({ error: 'Failed to process file' });
  }
};

const getExcel = async (req, res) => {
  try {
    const orders = await fetchOrders();
      if (!orders || orders.length === 0) {
        return res.status(404).json({ message: "No orders found" });
    }
    const buffer = await createExcelFromData(orders);
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', 'attachment; filename="orders.xlsx"');
    res.send(buffer);
  } catch (error) {
    console.error('Error creating Excel:', error);
    res.status(500).json({ error: 'Failed to create Excel' });
  }
};


export { uploadAndProcessExcel, getExcel };
```

**6. API エンドポイント (pages/api/excel.js)**

```javascript
// pages/api/excel.js
import { uploadAndProcessExcel, getExcel } from '../../controllers/excelController';
import multer from 'multer';
import nextConnect from 'next-connect';

const upload = multer({ storage: multer.memoryStorage() });
const uploadMiddleware = upload.single('file');


const handler = nextConnect({
    onError: (err, req, res, next) => {
        console.error(err.stack);
        res.status(500).json({ error: 'Something broke!'});
    },
    onNoMatch: (req, res) => {
        res.status(404).json({ error: 'Not found' });
    }
})
.use(uploadMiddleware)
.post(async (req, res) => {
    await uploadAndProcessExcel(req,res);
})
.get(async (req, res) => {
    await getExcel(req,res);
});

export default handler;


export const config = {
    api: {
        bodyParser: false,
    }
}
```

**7. ファイルアップロードコンポーネント (components/FileUpload.js)**

```jsx
// components/FileUpload.js
import { useState } from 'react';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('ファイルを選択してください。');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/excel', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        setMessage('ファイルが正常にアップロードされました。');
      } else {
        const errorData = await response.json();
        setMessage(`アップロードに失敗しました: ${errorData.error || 'エラーが発生しました'}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setMessage('アップロード中にエラーが発生しました。');
    }
  };

  return (
    <div>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>アップロード</button>
      {message && <p>{message}</p>}
    </div>
  );
};

export default FileUpload;
```

**8. Webページでコンポーネントを利用 (pages/index.js)**

```jsx
// pages/index.js
import FileUpload from '../components/FileUpload';

const Home = () => {
  const handleDownload = async () => {
    try {
        const response = await fetch('/api/excel', {
          method: 'GET',
        });
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'orders.xlsx';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
        } else {
            console.error("Failed to download excel file");
            const errorData = await response.json();
          console.error(`Failed to download excel file ${errorData.error || 'エラーが発生しました'}`);
        }
      } catch (error) {
        console.error("Error during download:", error);
    }
  };


  return (
    <div>
      <h1>Excelファイルアップロード</h1>
      <FileUpload />
      <button onClick={handleDownload}>Excelダウンロード</button>
    </div>
  );
};

export default Home;
```

**実装のポイント**

*   **機能1 (POST):**
    *   WebページからExcelファイルをアップロードし、S3に保存、DBに登録、完了後にS3に移動します。
*   **機能2 (GET):**
    *   DBからデータを取得し、Excelファイルを作成し、レスポンスとしてダウンロードさせます。
*   **共通:**
    *   3層アーキテクチャ（MVC）で実装します。
    *   S3操作、Excel操作、DBアクセスはそれぞれのサービス層で実装します。
    *   エラーハンドリングを適切に行います。

**使い方**

1.  **WebページでExcelファイルをアップロード (機能1):**
    *   `pages/index.js` の `FileUpload` コンポーネントを使って、Excelファイルを選択し、アップロードボタンをクリックします。
    *   ファイルがS3の `uploads` プレフィックスにアップロードされ、Excelファイルの内容が解析され、PostgreSQLに登録されます。
    *   登録完了後、S3上のファイルは `finished` プレフィックスに移動します。
2.  **WebページでExcelファイルをダウンロード (機能2):**
   *  `pages/index.js` のExcelダウンロードボタンをクリックすると、DBからデータを取得して作成されたExcelファイルがダウンロードされます。

**注意点**

*   Amazon S3のバケットとIAMの設定が必要です。
*   PostgreSQLの設定が正しく行われているかを確認してください。
*   `exceljs` のバージョンによっては、解析処理に調整が必要となる場合があります。
*  上記コードはあくまでベースとなるもので、実際の要件に合わせて調整が必要な場合があります。

この実装で、機能1と機能2の両方をカバーし、それぞれの要件を満たすことができています。
もし実装中に問題が発生したり、追加の機能が必要になった場合は、お気軽にご質問ください。
