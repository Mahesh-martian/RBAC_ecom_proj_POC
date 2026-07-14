import Image from "next/image";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="relative h-screen w-screen flex items-center justify-center bg-[#FDD403]">
      <Image
        src="/images/not-found.jpg"
        alt="Not-Found"
        height={500}
        width={800}
        className="absolute object-cover "
      />
      <div className="relative z-10 text-center mt-60 lg:mt-96">
        <Link href="/">
          <span className="bg-blue-500 text-white rounded-lg py-3 px-5 text-lg font-semibold">
            Back to Home
          </span>
        </Link>
      </div>
    </div>
  );
}
