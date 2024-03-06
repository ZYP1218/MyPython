import tkinter as tk
from tkinter import ttk, scrolledtext
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageTk
import io

class BarcodeGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.resizable(False, False)
        self.root.title("条码生成器")
        self.barcode_images = []
        self.scrolling = False
        self.configure_style()
        self.create_widgets()

    def configure_style(self):
        """配置应用程序的风格和主题"""
        style = ttk.Style()
        style.theme_use('clam')  # 使用clam主题
        style.configure('TButton', font=('Helvetica', 10), background='#E1E1E1', foreground='black')
        style.configure('TLabel', font=('Helvetica', 10), background='#E1E1E1', foreground='black')
        style.configure('TEntry', font=('Helvetica', 10), background='#FFFFFF', foreground='black')

    def update_barcode_count(self):
        """更新界面上的条码计数"""
        total = len(self.barcode_images)
        top_barcode_index = self.canvas_barcodes.yview()[0] * total
        self.total_barcodes_label.config(text=f"总条码数量：{total}")
        self.current_barcode_label.config(text=f"当前条码：{int(top_barcode_index) + 1 if self.barcode_images else 0}")

    def clear_barcodes(self):
        """清除画布上的所有条码"""
        if self.scrolling:
            return  # 如果正在滚动，则不执行任何操作
        self.canvas_barcodes.delete("all")
        self.barcode_images.clear()
        self.canvas_barcodes.config(scrollregion=(0, 0, self.canvas_barcodes.winfo_width(), 110))
        self.update_barcode_count()

    def generate_and_display_barcode(self):
        """生成条形码并在画布上显示"""
        if self.scrolling:
            return  # 如果正在滚动，则不执行任何操作
        content = self.text_area.get('1.0', tk.END).strip()
        self.clear_barcodes()
        y_position = 10
        if content:  # 检查文本域是否为空
            canvas_width = self.canvas_barcodes.winfo_width() if self.canvas_barcodes.winfo_width() > 0 else self.root.winfo_width()
            lines = content.split('\n')
            for line in lines:
                if line:
                    barcode_instance = Code128(line, writer=ImageWriter())
                    fp = io.BytesIO()
                    barcode_instance.write(fp)
                    fp.seek(0)
                    image = Image.open(fp)
                    image = image.resize((canvas_width, 100), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    self.barcode_images.append((barcode_instance, fp, photo))
                    self.canvas_barcodes.create_image(10, y_position, image=photo, anchor='nw')
                    y_position += 100 + 10
            self.canvas_barcodes.config(scrollregion=(0, 0, canvas_width, y_position))
            self.update_barcode_count()

    def create_widgets(self):
        """创建GUI组件"""
        # 创建输入提示标签
        label_top = ttk.Label(self.root, text="请输入要生成条码的文本（每行生成一个条码）：")
        label_top.pack(pady=(10, 5), padx=10, fill='x')

        # 创建文本输入区域
        self.text_area = scrolledtext.ScrolledText(self.root, height=10)
        self.text_area.pack(pady=(5, 10), padx=10, fill='x', expand=True)

        # 创建按钮框架
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=(0, 5), fill='x')

        # 创建生成和清除条码的按钮
        generate_button = ttk.Button(button_frame, text="生成条码", command=self.generate_and_display_barcode)
        generate_button.pack(side=tk.LEFT, padx=(0, 10), fill='x', expand=True)

        clear_button = ttk.Button(button_frame, text="清除条码", command=self.clear_barcodes)
        clear_button.pack(side=tk.LEFT, fill='x', expand=True)

        # 创建条码数量和当前条码的标签
        self.total_barcodes_label = ttk.Label(self.root, text="总条码数量：0")
        self.total_barcodes_label.pack(pady=(5, 0))

        self.current_barcode_label = ttk.Label(self.root, text="当前条码：0")
        self.current_barcode_label.pack(pady=(0, 5))

        # 创建画布和滚动条容器
        frame_barcodes = tk.Frame(self.root, bd=2, relief=tk.SUNKEN)
        frame_barcodes.pack(fill='both', expand=True, pady=(5, 0), padx=10)

        # 创建画布和滚动条
        self.canvas_barcodes = tk.Canvas(frame_barcodes, bg="white", height=110)
        self.canvas_barcodes.pack(side="left", fill='both', expand=True)
        # 绑定鼠标滚轮事件
        self.canvas_barcodes.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas_barcodes.config(scrollregion=(0, 0, 0, 110))

        scrollbar = ttk.Scrollbar(frame_barcodes, orient="vertical", command=self.canvas_barcodes.yview)
        self.canvas_barcodes.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # 创建滚动速度控制组件
        scroll_speed_frame = ttk.Frame(self.root)
        scroll_speed_frame.pack(pady=(0, 10), fill='x', padx=10)

        # 创建滚动按钮并放置到滚动速度框架中
        self.scroll_button = ttk.Button(scroll_speed_frame, text="开始滚动", command=self.toggle_scrolling)
        self.scroll_button.pack(side=tk.LEFT, fill='x', expand=True)

        # 绑定空格键按下事件处理程序
        self.root.bind('<space>', self.on_space_press)

        scroll_speed_label = ttk.Label(scroll_speed_frame, text="滚动速度:")
        scroll_speed_label.pack(side=tk.LEFT, padx=(0, 2))

        self.scroll_speed_entry = ttk.Entry(scroll_speed_frame, width=5)
        self.scroll_speed_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.scroll_speed_entry.insert(0, "1")  # 默认滚动速度

        # 绑定事件
        self.root.bind('<space>', self.on_space_press)

    def scroll_barcodes(self):
        """滚动条码图像，并在到达底部时停止"""
        if self.scrolling:
            # 获取当前滚动位置和画布可滚动区域的高度
            scroll_position = self.canvas_barcodes.yview()[1]
            canvas_scrollable_height = self.canvas_barcodes.bbox("all")[3] if self.canvas_barcodes.bbox("all") else 0

            # 检查是否已经滚动到底部
            if scroll_position >= 1.0 or (self.canvas_barcodes.winfo_height() >= canvas_scrollable_height):
                # 到达底部，停止滚动
                self.toggle_scrolling()
                return

            # 如果没有到达底部，继续滚动
            scroll_step = int(self.scroll_speed_entry.get()) if self.scroll_speed_entry.get().isdigit() else 1
            self.canvas_barcodes.yview_scroll(scroll_step, "units")
            self.root.after(100, self.scroll_barcodes)  # 继续在100毫秒后调用自身
            self.update_barcode_count()

    def on_mousewheel(self, event):
        """处理鼠标滚轮事件以滚动画布"""
        if self.root.tk.call('tk', 'windowingsystem') == 'x11':  # For Linux, use 'x11' instead of 'win32'
            delta = event.delta
        else:
            delta = -1 * event.delta  # 对于Windows, 滚动方向相反
        self.canvas_barcodes.yview_scroll(int(delta / 120), "units")
        self.update_barcode_count()  # 更新当前条码显示

    def toggle_scrolling(self):
        """切换滚动状态，并根据当前状态更新按钮文本和滚动功能"""
        self.scrolling = not self.scrolling
        if self.scrolling:
            self.scroll_button.config(text="停止滚动")
            self.scroll_barcodes()  # 开始滚动
        else:
            self.scroll_button.config(text="开始滚动")
            # 滚动停止，无需调用self.scroll_barcodes()

    def on_space_press(self, event):
        """当用户按下空格键时，切换滚动状态"""
        self.toggle_scrolling()

# 应用程序启动
if __name__ == '__main__':
    root = tk.Tk()
    app = BarcodeGeneratorApp(root)
    root.mainloop()

