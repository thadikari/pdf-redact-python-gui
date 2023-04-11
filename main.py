import os
import pathlib
from tkinter import *
from tkinter import filedialog

from PIL import ImageTk, ImageDraw
from pdf2image import convert_from_path


# https://stackoverflow.com/questions/29789554/tkinter-draw-rectangle-using-a-mouse
class ImageFrame(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.x = self.y = 0
        self.canvas = Canvas(self, cursor="cross")

        self.sbarv = Scrollbar(self, orient=VERTICAL)
        self.sbarh = Scrollbar(self, orient=HORIZONTAL)
        self.sbarv.config(command=self.canvas.yview)
        self.sbarh.config(command=self.canvas.xview)

        self.canvas.config(yscrollcommand=self.sbarv.set)
        self.canvas.config(xscrollcommand=self.sbarh.set)

        self.canvas.grid(row=0, column=0, sticky=N + S + E + W)
        self.sbarv.grid(row=0, column=1, stick=N + S)
        self.sbarh.grid(row=1, column=0, sticky=E + W)

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.rect_list = None
        self.drawing_rect = None
        self.start_x = None
        self.start_y = None

    def draw_rect(self, x1, y1, x2, y2):
        return self.canvas.create_rectangle(x1, y1, x2, y2, fill='black')

    def load(self, image, rect_list):
        # PIL.Image.open("C:\\Users\\Tharindu\\Desktop\\temp\\PXL_20220905_1801561901_2.jpg")
        self.wazil, self.lard = image.size
        self.canvas.config(scrollregion=(0, 0, self.wazil, self.lard))
        self.tk_im = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_im)

        self.rect_list = rect_list
        for rect in rect_list: self.draw_rect(*rect)

    def on_button_press(self, event):
        # save mouse drag start position
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.drawing_rect = self.draw_rect(self.x, self.y, 1, 1)

    def on_move_press(self, event):
        if self.drawing_rect is None: return
        # expand rectangle as you drag the mouse
        cur_x, cur_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.coords(self.drawing_rect, self.start_x, self.start_y, cur_x, cur_y)

        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if event.x > 0.9 * w:
            self.canvas.xview_scroll(1, 'units')
        elif event.x < 0.1 * w:
            self.canvas.xview_scroll(-1, 'units')
        if event.y > 0.9 * h:
            self.canvas.yview_scroll(1, 'units')
        elif event.y < 0.1 * h:
            self.canvas.yview_scroll(-1, 'units')

    def on_button_release(self, event):
        if self.drawing_rect is None: return
        if self.rect_list is None: return
        cur_x, cur_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.rect_list.append((self.start_x, self.start_y, cur_x, cur_y))
        self.drawing_rect = None


class Window:
    def __init__(self, master):
        # https://www.pythonguis.com/tutorials/use-tkinter-to-design-gui-layout/
        # Create left and right frames
        left_frame = Frame(master, width=200, height=400, bg='grey')
        left_frame.grid(row=0, column=0, padx=10, pady=5)

        image_frame = ImageFrame(master)
        image_frame.grid(row=0, column=1, padx=10, pady=5)

        # Create toolbar frame
        tool_bar = Frame(left_frame, width=180, height=185)
        tool_bar.grid(row=2, column=0, padx=5, pady=5)

        # Example labels that serve as placeholders for other widgets
        Button(tool_bar, text="Open", command=self.load_pdf, relief=RAISED) \
            .grid(row=0, column=0, padx=5, pady=3, ipadx=10)  # ipadx is padding inside the Label widget
        Button(tool_bar, text="Save", command=self.save_pdf, relief=RAISED) \
            .grid(row=0, column=1, padx=5, pady=3, ipadx=10)

        thumbs_scroll = Scrollbar(tool_bar)
        thumbs_scroll.grid(row=1, column=1, stick=N + S)
        thumbs_list = Listbox(tool_bar, yscrollcommand=thumbs_scroll.set)
        thumbs_list.grid(row=1, column=0)
        thumbs_scroll.config(command=thumbs_list.yview)
        on_select = lambda evt: self.on_select_thumb(int(evt.widget.curselection()[0]))
        thumbs_list.bind('<<ListboxSelect>>', on_select)

        self.data_list = []
        self.image_frame = image_frame
        self.thumbs_list = thumbs_list
        self.input_pdf_path = self.load_pdf()

    def load_pdf(self):
        # https://stackoverflow.com/questions/52961453/control-filetype-as-pdf-in-tkinter
        options = dict(defaultextension=".pdf", filetypes=[('pdf file', '*.pdf')])
        pdf_path = filedialog.askopenfilename(**options)
        if pdf_path is '' or not pathlib.Path(pdf_path).is_file(): return None

        self.data_list = [(img, []) for img in convert_from_path(pdf_path, 500)]

        self.thumbs_list.delete(0, END)
        for line in range(len(self.data_list)):
            self.thumbs_list.insert(END, "Page " + str(line + 1))

        if len(self.data_list) > 0:
            self.thumbs_list.selection_set(0)
            # trigger event manually
            self.on_select_thumb(0)

        return pdf_path

    def on_select_thumb(self, index):
        self.image_frame.load(*self.data_list[index])

    def save_pdf(self):
        if self.input_pdf_path is None: return

        name, _ = os.path.splitext(os.path.basename(self.input_pdf_path))
        base_name = f'{name}_redact.pdf'
        options = dict(defaultextension=".pdf",
                       filetypes=[('pdf file', '*.pdf')],
                       initialfile=base_name,
                       initialdir=os.path.dirname(self.input_pdf_path))
        pdf_path = filedialog.asksaveasfilename(**options)
        if pdf_path is '': return

        im_list = []
        for img, rects in self.data_list:
            img_copy = img.copy()
            draw = ImageDraw.Draw(img_copy)
            for x1, y1, x2, y2 in rects:
                draw.rectangle(((x1, y1), (x2, y2)), fill='black')
            im_list.append(img_copy)
        im_list[0].save(pdf_path, "pdf", resolution=100.0, save_all=True, append_images=im_list[1:])


def main():
    root = Tk()  # create root window
    root.title("Redact PDF")  # title of the GUI window
    root.geometry('1200x800')
    # root.maxsize(900, 600)  # specify the max size the window can expand to
    root.config(bg="skyblue")  # specify background color
    Window(root)
    root.mainloop()


if __name__ == "__main__":
    main()
